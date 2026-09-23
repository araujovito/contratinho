"""Enriquecimento pela rota de item do PNCP — sem rede.

As respostas são sintéticas: a API respondeu 502/503 durante todo o
desenvolvimento deste módulo. Ver a ressalva no docs/WEB.md.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.utils import timezone

from radar_pncp.web import documentos
from radar_pncp.web.models import Opportunity

DETALHE = {
    "dataAberturaProposta": "2026-09-18T08:00:00",
    "dataEncerramentoProposta": "2026-10-03T18:00:00",
    "dataPublicacaoPncp": "2026-09-17T09:00:00",
    "valorTotalEstimado": 42000.5,
    "modalidadeNome": "Pregão - Eletrônico",
}

ARQUIVOS = [
    {
        "titulo": "Edital 12/2026",
        "tipoDocumentoNome": "Edital",
        "url": "https://pncp.gov.br/pncp-api/v1/orgaos/1/compras/2026/12/arquivos/1",
        "sequencialDocumento": 1,
    },
    {
        "titulo": "Termo de referência",
        "tipoDocumentoNome": "Anexo",
        "uri": "https://pncp.gov.br/pncp-api/v1/orgaos/1/compras/2026/12/arquivos/2",
    },
]


class Resposta:
    def __init__(self, corpo, status=200):
        self._corpo = corpo
        self.status_code = status

    def json(self):
        if self._corpo is None:
            raise ValueError("sem json")
        return self._corpo


class Cliente:
    """Devolve detalhe e arquivos conforme o caminho pedido."""

    def __init__(self, detalhe=DETALHE, arquivos=ARQUIVOS, status=200):
        self.detalhe, self.arquivos, self.status = detalhe, arquivos, status
        self.chamadas: list[str] = []

    def get(self, url, timeout=None):
        self.chamadas.append(url)
        if self.status != 200:
            return Resposta(None, self.status)
        corpo = self.arquivos if url.endswith("/arquivos") else self.detalhe
        return Resposta(corpo)


def nova(**campos) -> Opportunity:
    padrao = dict(
        pncp_id="12345678000190-1-000012/2026",
        title="Serviço de limpeza predial",
        agency="Órgão exemplo",
        uf="RJ",
        deadline=date(2027, 2, 5),  # veio da vigência: longe demais
        proposal_opening_date=date(2026, 2, 6),
        publication_date=date(2025, 2, 6),
        fetched_at=timezone.now(),
    )
    return Opportunity.objects.create(**{**padrao, **campos})


# --- identificador ----------------------------------------------------------


def test_quebra_identificador_pncp():
    assert documentos.partes_do_id("29138377000193-1-000001/2026") == (
        "29138377000193",
        2026,
        1,
    )


@pytest.mark.parametrize("ruim", ["", "sem-formato", "123-1-1/2026", None])
def test_identificador_invalido_avisa(ruim):
    with pytest.raises(documentos.DadosIndisponiveis, match="formato"):
        documentos.partes_do_id(ruim)


# --- leitura da API ---------------------------------------------------------


def test_detalhe_traz_datas_de_proposta_e_valor():
    dados = documentos.consultar("12345678000190-1-000012/2026", client=Cliente())
    assert dados["abertura"] == date(2026, 9, 18)
    assert dados["encerramento"] == date(2026, 10, 3)
    assert dados["valor"] == 42000.5


def test_arquivos_aceitam_url_e_uri():
    dados = documentos.consultar("12345678000190-1-000012/2026", client=Cliente())
    assert [a["titulo"] for a in dados["arquivos"]] == ["Edital 12/2026", "Termo de referência"]
    assert all(a["url"].startswith("https://") for a in dados["arquivos"])


def test_arquivo_sem_endereco_e_descartado():
    cliente = Cliente(arquivos=[{"titulo": "Sem link"}, ARQUIVOS[0]])
    dados = documentos.consultar("12345678000190-1-000012/2026", client=cliente)
    assert len(dados["arquivos"]) == 1


def test_pncp_fora_do_ar_levanta_dados_indisponiveis():
    with pytest.raises(documentos.DadosIndisponiveis, match="503"):
        documentos.consultar("12345678000190-1-000012/2026", client=Cliente(status=503))


# --- enriquecimento ---------------------------------------------------------


@pytest.mark.django_db
def test_enriquecer_substitui_datas_de_vigencia_pelas_de_proposta():
    item = nova()
    assert documentos.enriquecer(item, client=Cliente()) is True
    item.refresh_from_db()
    assert item.deadline == date(2026, 10, 3)
    assert item.proposal_opening_date == date(2026, 9, 18)
    assert item.publication_date == date(2026, 9, 17)
    assert item.value == 42000.5
    assert item.has_official_dates


@pytest.mark.django_db
def test_enriquecer_guarda_os_anexos():
    item = nova()
    documentos.enriquecer(item, client=Cliente())
    item.refresh_from_db()
    assert len(item.documents) == 2
    assert item.documents[0]["tipo"] == "Edital"


@pytest.mark.django_db
def test_pncp_fora_do_ar_nao_apaga_o_que_ja_existia():
    # a página precisa continuar de pé com o dado antigo
    item = nova()
    assert documentos.enriquecer(item, client=Cliente(status=503)) is False
    item.refresh_from_db()
    assert item.deadline == date(2027, 2, 5)
    assert item.documents == []
    assert item.enriched_at is None
    assert item.enrichment_checked_at is not None


@pytest.mark.django_db
def test_edital_sem_anexo_ainda_aproveita_as_datas():
    item = nova()
    assert documentos.enriquecer(item, client=Cliente(arquivos=[])) is True
    item.refresh_from_db()
    assert item.documents == []
    assert item.deadline == date(2026, 10, 3)


@pytest.mark.django_db
def test_valor_ja_conhecido_nao_e_sobrescrito():
    item = nova(value=1000)
    documentos.enriquecer(item, client=Cliente())
    item.refresh_from_db()
    assert item.value == 1000


# --- quando reconsultar -----------------------------------------------------


@pytest.mark.django_db
def test_consulta_no_primeiro_clique():
    assert documentos.precisa_enriquecer(nova()) is True


@pytest.mark.django_db
def test_nao_reconsulta_a_cada_clique():
    item = nova(enrichment_checked_at=timezone.now())
    assert documentos.precisa_enriquecer(item) is False


@pytest.mark.django_db
def test_reconsulta_depois_do_intervalo():
    # prazo prorrogado e errata publicada precisam aparecer algum dia
    item = nova(enrichment_checked_at=timezone.now() - timedelta(hours=7))
    assert documentos.precisa_enriquecer(item) is True


@pytest.mark.django_db
def test_falha_tambem_segura_a_proxima_tentativa():
    # PNCP instável não pode virar uma consulta por clique
    item = nova()
    documentos.enriquecer(item, client=Cliente(status=503))
    item.refresh_from_db()
    assert documentos.precisa_enriquecer(item) is False
