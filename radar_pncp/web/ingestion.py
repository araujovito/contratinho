"""Publicação atômica do catálogo; nenhum acesso à rede dentro da transação."""

from decimal import Decimal
from urllib.parse import urlsplit

from django.db import transaction
from django.utils import timezone

from radar_pncp.config import Perfil
from radar_pncp.filtro import aplicar_perfil

from .models import Market, Opportunity


def official_url(value):
    parsed = urlsplit(value or "")
    if parsed.scheme == "https" and parsed.netloc == "pncp.gov.br":
        return value
    return ""


@transaction.atomic
def publish(items):
    markets = [
        (market, Perfil(nome=market.name, termos=market.terms, excluir=market.exclusions))
        for market in Market.objects.all()
    ]
    now = timezone.now()
    count = 0
    for item in items:
        if not item.id or item.id == "None-None-None":
            raise ValueError("Contratação sem identificador válido; catálogo preservado.")
        opportunity, _ = Opportunity.objects.update_or_create(
            pncp_id=item.id,
            defaults={
                "title": item.objeto,
                "agency": item.orgao,
                "uf": item.uf or "",
                "value": Decimal(str(item.valor)) if item.valor is not None else None,
                "publication_date": item.publicacao,
                "proposal_opening_date": item.abertura,
                "deadline": item.encerramento,
                "official_url": official_url(item.url),
                "fetched_at": now,
            },
        )
        opportunity.markets.set(
            [market for market, profile in markets if aplicar_perfil(item, profile)]
        )
        count += 1
    return count
