"""Coleta pela API de busca usada pelo próprio portal público do PNCP."""

from __future__ import annotations

import time
from datetime import date, datetime
from typing import Any

from curl_cffi import requests
from curl_cffi.requests.errors import RequestsError

from contratinho.filtro import Licitacao

from .models import Market

SEARCH_URL = "https://www.pncp.gov.br/api/search/"
PAGE_SIZE = 50


def _date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.fromisoformat(value).date()


def _url(item: dict[str, Any]) -> str | None:
    cnpj = item.get("orgao_cnpj")
    year = item.get("ano")
    sequence = item.get("numero_sequencial")
    if not all((cnpj, year, sequence)):
        return None
    return f"https://pncp.gov.br/app/editais/{cnpj}/{year}/{sequence}"


def _to_opportunity(item: dict[str, Any]) -> Licitacao | None:
    identifier = item.get("numero_controle_pncp")
    if not identifier:
        return None
    value = item.get("valor_global")
    return Licitacao(
        id=identifier,
        objeto=item.get("description") or item.get("title") or "",
        orgao=item.get("orgao_nome") or item.get("unidade_nome") or "Órgão não informado",
        uf=item.get("uf"),
        modalidade=item.get("modalidade_licitacao_nome") or "",
        modalidade_id=(
            int(item["modalidade_licitacao_id"]) if item.get("modalidade_licitacao_id") else None
        ),
        valor=float(value) if value is not None else None,
        encerramento=_date(item.get("data_fim_vigencia")),
        publicacao=_date(item.get("data_publicacao_pncp")),
        url=_url(item),
        abertura=_date(item.get("data_inicio_vigencia")),
    )


def _request(
    client: requests.Session,
    params: dict[str, Any],
    *,
    retries: int = 6,
    pause: float = 2.0,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = client.get(SEARCH_URL, params=params)
            response.raise_for_status()
            return response.json()
        except RequestsError as error:
            last_error = error
            response = getattr(error, "response", None)
            if response is not None and response.status_code < 500:
                raise
            if attempt + 1 < retries:
                time.sleep(pause * (attempt + 1))
    raise RuntimeError("A busca do PNCP falhou após seis tentativas.") from last_error


def buscar_mercados(
    markets: list[Market],
    *,
    uf: str = "RJ",
    max_pages_per_term: int = 4,
    client: requests.Session | None = None,
    pause: float = 0.2,
    retry_pause: float = 2.0,
) -> list[Licitacao]:
    """Busca editais abertos por termo e remove duplicatas pelo identificador PNCP."""
    own_client = client is None
    # O balanceador do PNCP encerra repetidamente conexões de clientes HTTP
    # genéricos. A mesma rota responde ao navegador; por isso reproduzimos sua
    # negociação TLS em vez de aumentar indefinidamente o tempo de espera.
    client = client or requests.Session(impersonate="chrome")
    found: dict[str, Licitacao] = {}
    requested = False
    try:
        terms = dict.fromkeys(term for market in markets for term in market.terms)
        for term in terms:
            for page in range(1, max_pages_per_term + 1):
                requested = True
                payload = _request(
                    client,
                    {
                        "q": term,
                        "tipos_documento": "edital",
                        "status": "recebendo_proposta",
                        "ufs": uf,
                        "pagina": page,
                        "tam_pagina": PAGE_SIZE,
                    },
                    pause=retry_pause,
                )
                items = payload.get("items", [])
                for raw in items:
                    opportunity = _to_opportunity(raw)
                    if opportunity:
                        found[opportunity.id] = opportunity
                if not items or page * PAGE_SIZE >= payload.get("total", 0):
                    break
                time.sleep(pause)
            time.sleep(pause)
    finally:
        if own_client:
            client.close()
    if not requested:
        raise RuntimeError("Nenhum mercado possui termos para consultar no PNCP.")
    return list(found.values())
