"""Testes da camada de rede — sem rede.

A resposta do PNCP é servida de fixture via um httpx.MockTransport, então o CI
exercita paginação, parsing e tradução sem depender de o PNCP estar de pé.
"""

from __future__ import annotations

import httpx
import pytest
from exemplos import CONFIG_TESTE
from pypncp import PNCPClient
from pypncp.models import Contratacao

from radar_pncp import config as cfg
from radar_pncp import fonte
from radar_pncp.filtro import filtrar

CONFIG = cfg.carregar_texto(CONFIG_TESTE)


@pytest.fixture
def cliente_falso(pagina_proposta, monkeypatch):
    """PNCPClient apontado para um transporte que devolve a fixture."""
    chamadas: list[httpx.Request] = []

    def responder(request: httpx.Request) -> httpx.Response:
        chamadas.append(request)
        return httpx.Response(200, json=pagina_proposta)

    transporte = httpx.MockTransport(responder)

    def construir(*args, **kwargs):
        return PNCPClient(http_client=httpx.AsyncClient(transport=transporte))

    monkeypatch.setattr(fonte.PNCPClient, "builder", lambda: _BuilderFalso(construir))
    return chamadas


class _BuilderFalso:
    def __init__(self, construir):
        self._construir = construir

    def timeout(self, _valor):
        return self

    def build(self):
        return self._construir()


def test_traducao_do_dto(pagina_proposta):
    contratacao = Contratacao.model_validate(pagina_proposta["data"][0])
    licitacao = fonte.para_licitacao(contratacao)
    assert licitacao.id == "12345678000190-1-000123/2026"
    assert licitacao.uf == "SP"
    assert licitacao.orgao == "MUNICIPIO DE EXEMPLO"
    assert licitacao.modalidade_id == 6
    assert licitacao.valor == 184500.0
    assert str(licitacao.publicacao) == "2026-09-15"
    assert str(licitacao.abertura) == "2026-09-16"
    assert "cartilhas" in licitacao.objeto
    assert licitacao.complemento.startswith("Tiragem")
    assert licitacao.url == "https://pncp.gov.br/app/editais/12345678000190/2026/123"


def test_id_cai_para_cnpj_ano_sequencial_sem_numero_de_controle(pagina_proposta):
    bruto = dict(pagina_proposta["data"][0], numeroControlePNCP=None)
    licitacao = fonte.para_licitacao(Contratacao.model_validate(bruto))
    assert licitacao.id == "12345678000190-2026-123"


def test_campos_ausentes_nao_quebram_a_traducao():
    licitacao = fonte.para_licitacao(Contratacao.model_validate({}))
    assert licitacao.objeto == ""
    assert licitacao.orgao == "(órgão não informado)"
    assert licitacao.valor is None
    assert licitacao.url is None


@pytest.mark.asyncio
async def test_buscar_devolve_licitacoes_traduzidas(cliente_falso):
    from datetime import date

    licitacoes = await fonte.buscar_async(CONFIG, ate=date(2026, 10, 31))
    assert len(licitacoes) == 4
    assert [licitacao.uf for licitacao in licitacoes] == ["SP", "SP", "CE", "MG"]


@pytest.mark.asyncio
async def test_uma_chamada_por_modalidade_configurada(cliente_falso):
    from datetime import date

    configuracao = cfg.carregar_texto(
        "[radar]\nmodalidades = [6, 8]\n[[perfil]]\nnome='x'\ntermos=['impressão']\n"
    )
    await fonte.buscar_async(configuracao, ate=date(2026, 10, 31))
    codigos = [request.url.params.get("codigoModalidadeContratacao") for request in cliente_falso]
    assert set(codigos) == {"6", "8"}


@pytest.mark.asyncio
async def test_sem_modalidade_configurada_nao_manda_o_parametro(cliente_falso):
    from datetime import date

    await fonte.buscar_async(CONFIG, ate=date(2026, 10, 31))
    assert "codigoModalidadeContratacao" not in cliente_falso[0].url.params


@pytest.mark.asyncio
async def test_mesma_licitacao_em_duas_modalidades_nao_duplica(cliente_falso):
    from datetime import date

    configuracao = cfg.carregar_texto(
        "[radar]\nmodalidades = [6, 8]\n[[perfil]]\nnome='x'\ntermos=['impressão']\n"
    )
    licitacoes = await fonte.buscar_async(configuracao, ate=date(2026, 10, 31))
    assert len({licitacao.id for licitacao in licitacoes}) == len(licitacoes) == 4


@pytest.mark.asyncio
async def test_ponta_a_ponta_da_fixture_ate_os_achados(cliente_falso):
    """O caminho inteiro sem rede: resposta do PNCP -> achados filtrados."""
    from datetime import date

    licitacoes = await fonte.buscar_async(CONFIG, ate=date(2026, 10, 31))
    achados = filtrar(licitacoes, CONFIG)

    # sobra só a das cartilhas: a das impressoras é excluída, a do papel é CE
    # (fora da UF) e a dos folders não informa valor (mínimo de R$ 10.000)
    assert [(a.perfil, a.termos) for a in achados] == [("impressos", ("impressão", "cartilha"))]
