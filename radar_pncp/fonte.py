"""Consulta ao PNCP via pypncp e tradução para o modelo do radar.

Este é o único módulo que fala com a rede. Ele devolve `Licitacao`, para que
`filtro` e `estado` nunca precisem conhecer a API nem a biblioteca.
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta

from pypncp import PNCPClient
from pypncp.models import Contratacao

from radar_pncp.config import Config
from radar_pncp.filtro import Licitacao

# A consulta /contratacoes/proposta devolve o que ainda recebe proposta até
# `data_final`. A janela padrão é curta de propósito: edital que encerra daqui
# a três meses não é urgência, é ruído diário.
JANELA_PADRAO_DIAS = 30


def _url(contratacao: Contratacao) -> str | None:
    if not contratacao.orgao_cnpj:
        return None
    return (
        f"https://pncp.gov.br/app/editais/{contratacao.orgao_cnpj}"
        f"/{contratacao.ano_compra}/{contratacao.sequencial_compra}"
    )


def para_licitacao(contratacao: Contratacao) -> Licitacao:
    """Traduz o DTO do PNCP para o modelo interno."""
    identificador = contratacao.numero_controle_pncp or (
        f"{contratacao.orgao_cnpj}-{contratacao.ano_compra}-{contratacao.sequencial_compra}"
    )
    publicacao = contratacao.data_publicacao_pncp
    abertura = contratacao.data_abertura_proposta
    return Licitacao(
        id=identificador,
        objeto=contratacao.objeto_compra or "",
        orgao=contratacao.orgao_nome or contratacao.unidade_nome or "(órgão não informado)",
        uf=contratacao.orgao_uf,
        modalidade=contratacao.modalidade_nome or "",
        modalidade_id=contratacao.modalidade_id,
        valor=contratacao.valor_total_estimado,
        # O DTO do pypncp não expõe dataEncerramentoProposta; o prazo fica
        # garantido pela janela da consulta. Ver ROADMAP.
        encerramento=None,
        publicacao=publicacao.date() if publicacao else None,
        complemento=contratacao.informacao_complementar or "",
        url=_url(contratacao),
        abertura=abertura.date() if abertura else None,
    )


async def buscar_async(config: Config, *, ate: date, timeout: int = 30) -> list[Licitacao]:
    """Baixa as contratações com proposta aberta até `ate`.

    Se a config restringe modalidades, consulta uma por vez — a API aceita um
    único código por chamada. Sem restrição, uma chamada só, sem filtro.
    """
    modalidades: list[int | None] = list(config.radar.modalidades) or [None]
    vistos: set[str] = set()
    licitacoes: list[Licitacao] = []

    async with PNCPClient.builder().timeout(timeout).build() as cliente:
        for modalidade in modalidades:
            async for contratacao in cliente.contratacoes.list_all_com_proposta(
                data_final=ate, codigo_modalidade=modalidade
            ):
                licitacao = para_licitacao(contratacao)
                if licitacao.id in vistos:
                    continue
                vistos.add(licitacao.id)
                licitacoes.append(licitacao)
    return licitacoes


def buscar(
    config: Config, *, dias: int = JANELA_PADRAO_DIAS, hoje: date | None = None
) -> list[Licitacao]:
    """Versão síncrona, para a CLI."""
    referencia = hoje or date.today()
    return asyncio.run(buscar_async(config, ate=referencia + timedelta(days=dias)))
