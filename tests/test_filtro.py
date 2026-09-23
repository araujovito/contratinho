from __future__ import annotations

from datetime import date

import pytest
from exemplos import CONFIG_TESTE

from radar_pncp import config as cfg
from radar_pncp.filtro import (
    Licitacao,
    aplicar_perfil,
    casa,
    filtrar,
    normalizar,
    passa_filtros_globais,
    termos_encontrados,
)

CONFIG = cfg.carregar_texto(CONFIG_TESTE)
IMPRESSOS, PAPEL = CONFIG.perfil


def licitacao(objeto: str, **campos) -> Licitacao:
    padrao = dict(
        id="PNCP-1",
        objeto=objeto,
        orgao="Prefeitura de Exemplo",
        uf="SP",
        modalidade="Pregão - Eletrônico",
        modalidade_id=6,
        valor=50_000.0,
        encerramento=date(2026, 10, 1),
        publicacao=date(2026, 9, 1),
    )
    return Licitacao(**{**padrao, **campos})


# --- normalização -----------------------------------------------------------


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("Aquisição de  PAPEL", "aquisicao de papel"),
        ("IMPRESSÃO\nde folders", "impressao de folders"),
        ("  serviços gráficos  ", "servicos graficos"),
    ],
)
def test_normalizar(entrada, esperado):
    assert normalizar(entrada) == esperado


# --- casamento de termo -----------------------------------------------------


def test_casa_ignora_acento_e_caixa():
    assert casa("Serviço de IMPRESSAO digital", "impressão")


def test_casa_aceita_plural():
    assert casa("contratação de gráficas rápidas", "gráfica")


def test_casa_exige_palavra_inteira():
    # o caso que motiva `excluir`: 'impressão' não pode casar com 'impressora'
    assert not casa("aquisição de impressora multifuncional", "impressão")


def test_casa_termo_de_varias_palavras():
    assert casa("compra de PAPEL  SULFITE A4", "papel sulfite")
    assert not casa("compra de papel para sulfite", "papel sulfite")


def test_casa_tolera_hifen_e_barra():
    assert casa("papel-sulfite branco", "papel sulfite")


def test_termos_encontrados_preserva_a_ordem_do_perfil():
    texto = "Serviço de impressão de cartilha e folder"
    assert termos_encontrados(texto, IMPRESSOS.termos) == ("impressão", "folder", "cartilha")


# --- perfis -----------------------------------------------------------------


def test_perfil_casa_e_registra_o_termo():
    achado = aplicar_perfil(licitacao("Serviço de impressão de cartilhas"), IMPRESSOS)
    assert achado is not None
    assert achado.perfil == "impressos"
    assert achado.termos == ("impressão", "cartilha")


def test_excluir_vence_o_termo():
    # 'impressão' casa, mas 'toner' está na lista de exclusão: descarta
    assert aplicar_perfil(licitacao("Impressão e recarga de toner"), IMPRESSOS) is None


def test_perfil_sem_casamento_devolve_none():
    assert aplicar_perfil(licitacao("Aquisição de merenda escolar"), IMPRESSOS) is None


def test_informacao_complementar_tambem_e_procurada():
    achado = aplicar_perfil(
        licitacao("Aquisição de material", complemento="inclui papel offset 90g"), PAPEL
    )
    assert achado is not None


# --- filtros globais --------------------------------------------------------


@pytest.mark.parametrize(
    "campos,passa",
    [
        ({}, True),
        ({"uf": "RJ"}, False),
        ({"uf": None}, False),
        ({"valor": 9_999.0}, False),
        ({"valor": 10_000.0}, True),
        ({"valor": None}, False),  # sem valor não dá para provar que atinge o mínimo
    ],
)
def test_filtros_globais(campos, passa):
    assert passa_filtros_globais(licitacao("impressão", **campos), CONFIG) is passa


def test_modalidade_filtra_quando_configurada():
    configuracao = cfg.carregar_texto(
        "[radar]\nmodalidades = [6]\n[[perfil]]\nnome='x'\ntermos=['impressão']\n"
    )
    assert passa_filtros_globais(licitacao("impressão", modalidade_id=6), configuracao)
    assert not passa_filtros_globais(licitacao("impressão", modalidade_id=8), configuracao)


def test_valor_maximo_nao_descarta_quem_nao_informa_valor():
    configuracao = cfg.carregar_texto(
        "[radar]\nvalor_maximo = 100\n[[perfil]]\nnome='x'\ntermos=['impressão']\n"
    )
    assert passa_filtros_globais(licitacao("impressão", valor=None), configuracao)


# --- pipeline ---------------------------------------------------------------


def test_filtrar_aplica_global_antes_do_perfil():
    entradas = [
        licitacao("Impressão de cartilhas", id="a"),
        licitacao("Impressão de cartilhas", id="b", uf="BA"),  # fora da UF
        licitacao("Aquisição de impressora", id="c"),  # excluído
        licitacao("Papel sulfite A4", id="d"),
        licitacao("Impressão de folder", id="e", valor=500.0),  # abaixo do mínimo
    ]
    achados = filtrar(entradas, CONFIG)
    assert [(a.licitacao.id, a.perfil) for a in achados] == [("a", "impressos"), ("d", "papel")]


def test_uma_licitacao_rende_no_maximo_um_achado():
    # 'impressão em papel sulfite' casa com os dois perfis; vale o primeiro
    achados = filtrar([licitacao("Impressão em papel sulfite")], CONFIG)
    assert len(achados) == 1
    assert achados[0].perfil == "impressos"
