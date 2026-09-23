"""Seleção e envio do aviso de oportunidades novas.

O problema que abriu o projeto foi "quem esquece de olhar, perde o prazo". Um
site não resolve isso: ele exige que a pessoa lembre de entrar. É este módulo
que fecha a promessa.

Separado do comando de linha porque a escolha de *o que* avisar é regra de
negócio testável, e o envio em si é detalhe de entrega.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from radar_pncp.filtro import termos_encontrados

from .models import Alert, Opportunity, Preference

# Um e-mail com trinta editais não é aviso, é outra caixa de entrada para
# ignorar. O resto continua no site, e o e-mail diz quantos ficaram lá.
LIMITE_POR_AVISO = 8


@dataclass(frozen=True)
class Aviso:
    """O que vai para uma pessoa numa rodada."""

    user: object
    preference: Preference
    oportunidades: list[Opportunity]
    restantes: int

    @property
    def assunto(self) -> str:
        quantidade = len(self.oportunidades) + self.restantes
        if quantidade == 1:
            return "1 oportunidade nova para o seu negócio"
        return f"{quantidade} oportunidades novas para o seu negócio"


def candidatas(preference: Preference) -> list[Opportunity]:
    """Oportunidades do mercado da pessoa que ainda não foram avisadas a ela.

    Prazo vencido nunca entra: avisar sobre edital que fechou é pior do que
    não avisar, porque gasta a confiança que faz a pessoa abrir o próximo.
    """
    hoje = timezone.localdate()
    itens = Opportunity.objects.filter(markets=preference.market).filter(
        Q(deadline__gte=hoje) | Q(deadline__isnull=True)
    )
    if preference.uf:
        itens = itens.filter(uf=preference.uf)
    avisadas = Alert.objects.filter(user=preference.user).values_list("opportunity_id", flat=True)
    return list(itens.exclude(pk__in=avisadas).order_by("deadline", "-fetched_at"))


def montar(preference: Preference, *, limite: int = LIMITE_POR_AVISO) -> Aviso | None:
    """Monta o aviso de uma pessoa, ou None se não há nada novo."""
    novas = candidatas(preference)
    if not novas:
        return None
    escolhidas = novas[:limite]
    for item in escolhidas:
        item.match_terms = termos_encontrados(item.title, preference.market.terms)
    return Aviso(
        user=preference.user,
        preference=preference,
        oportunidades=escolhidas,
        restantes=max(0, len(novas) - limite),
    )


def _mensagem(aviso: Aviso) -> EmailMultiAlternatives:
    site = settings.RADAR_SITE_URL
    contexto = {
        "aviso": aviso,
        "site": site,
        "url_lista": f"{site}{reverse('opportunities')}",
        "url_interesses": f"{site}{reverse('preferences')}",
        "detalhe": lambda pk: f"{site}{reverse('detail', args=[pk])}",
    }
    corpo = render_to_string("radar/email/alerta.txt", contexto)
    mensagem = EmailMultiAlternatives(
        subject=aviso.assunto,
        body=corpo,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[aviso.user.email],
    )
    mensagem.attach_alternative(render_to_string("radar/email/alerta.html", contexto), "text/html")
    return mensagem


def enviar(aviso: Aviso, *, registrar: bool = True) -> bool:
    """Envia e marca como avisado. Devolve se o envio saiu.

    A marcação só acontece depois do envio dar certo: se o SMTP recusar, o
    edital volta na próxima rodada. Repetir incomoda, perder o prazo custa
    dinheiro — é a mesma escolha do `estado.py` da CLI.
    """
    if not aviso.user.email:
        return False
    enviados = _mensagem(aviso).send(fail_silently=False)
    if not enviados:
        return False
    if registrar:
        Alert.objects.bulk_create(
            [Alert(user=aviso.user, opportunity=item) for item in aviso.oportunidades],
            ignore_conflicts=True,
        )
    return True


def rodada(*, limite: int = LIMITE_POR_AVISO, seco: bool = False) -> dict[str, int]:
    """Percorre quem tem interesse definido e e-mail, e avisa o que é novo."""
    resumo = {"pessoas": 0, "avisos": 0, "oportunidades": 0, "falhas": 0}
    preferencias = (
        Preference.objects.select_related("user", "market")
        .exclude(user__email="")
        .filter(user__is_active=True)
    )
    for preference in preferencias:
        resumo["pessoas"] += 1
        aviso = montar(preference, limite=limite)
        if aviso is None:
            continue
        if seco:
            resumo["avisos"] += 1
            resumo["oportunidades"] += len(aviso.oportunidades)
            continue
        try:
            if enviar(aviso):
                resumo["avisos"] += 1
                resumo["oportunidades"] += len(aviso.oportunidades)
            else:
                resumo["falhas"] += 1
        except Exception:  # SMTP fora do ar não pode derrubar a rodada inteira
            resumo["falhas"] += 1
    return resumo


def sem_email() -> int:
    """Quantas contas com interesse definido ainda não têm endereço."""
    return (
        get_user_model()
        .objects.filter(preference__isnull=False)
        .filter(Q(email="") | Q(email__isnull=True))
        .count()
    )
