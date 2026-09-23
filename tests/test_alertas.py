"""Aviso por e-mail — a parte que faz o Radar ser um radar.

Nada aqui toca a rede: o Django guarda as mensagens em `mail.outbox`.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from contratinho.web import alertas
from contratinho.web.models import Alert, Market, Opportunity, Preference

pytestmark = pytest.mark.django_db


def mercado() -> Market:
    return Market.objects.get(slug="limpeza")


def pessoa(django_user_model, email="alguem@exemplo.com", uf="RJ"):
    user = django_user_model.objects.create_user("alguem", email=email, password="senha-longa-42")
    Preference.objects.create(user=user, market=mercado(), uf=uf)
    return user


def edital(titulo="Serviço de limpeza predial", **campos) -> Opportunity:
    padrao = dict(
        pncp_id=f"12345678000190-1-{Opportunity.objects.count():06d}/2026",
        title=titulo,
        agency="Prefeitura de Exemplo",
        uf="RJ",
        deadline=timezone.localdate() + timedelta(days=10),
        fetched_at=timezone.now(),
    )
    item = Opportunity.objects.create(**{**padrao, **campos})
    item.markets.add(mercado())
    return item


# --- o que entra no aviso ---------------------------------------------------


def test_avisa_oportunidade_nova(django_user_model):
    user = pessoa(django_user_model)
    edital()
    aviso = alertas.montar(Preference.objects.get(user=user))
    assert aviso is not None
    assert len(aviso.oportunidades) == 1


def test_nao_avisa_duas_vezes(django_user_model):
    user = pessoa(django_user_model)
    item = edital()
    Alert.objects.create(user=user, opportunity=item)
    assert alertas.montar(Preference.objects.get(user=user)) is None


def test_prazo_vencido_nunca_entra(django_user_model):
    """Avisar sobre edital fechado gasta a confiança que abre o próximo e-mail."""
    user = pessoa(django_user_model)
    edital(deadline=timezone.localdate() - timedelta(days=1))
    assert alertas.montar(Preference.objects.get(user=user)) is None


def test_respeita_a_uf_escolhida(django_user_model):
    user = pessoa(django_user_model, uf="MG")
    edital(uf="RJ")
    assert alertas.montar(Preference.objects.get(user=user)) is None


def test_respeita_o_mercado_escolhido(django_user_model):
    user = pessoa(django_user_model)
    item = edital()
    item.markets.set([Market.objects.get(slug="alimentacao")])
    assert alertas.montar(Preference.objects.get(user=user)) is None


def test_limita_o_tamanho_e_conta_o_resto(django_user_model):
    # e-mail com trinta editais não é aviso, é outra caixa para ignorar
    user = pessoa(django_user_model)
    for _ in range(11):
        edital()
    aviso = alertas.montar(Preference.objects.get(user=user), limite=8)
    assert len(aviso.oportunidades) == 8
    assert aviso.restantes == 3
    assert "11 oportunidades" in aviso.assunto


def test_assunto_no_singular(django_user_model):
    user = pessoa(django_user_model)
    edital()
    assert alertas.montar(Preference.objects.get(user=user)).assunto.startswith("1 oportunidade n")


def test_prazo_mais_curto_vem_primeiro(django_user_model):
    user = pessoa(django_user_model)
    longe = edital(deadline=timezone.localdate() + timedelta(days=30))
    perto = edital(deadline=timezone.localdate() + timedelta(days=2))
    aviso = alertas.montar(Preference.objects.get(user=user))
    assert [o.pk for o in aviso.oportunidades] == [perto.pk, longe.pk]


# --- envio ------------------------------------------------------------------


def test_envio_monta_texto_e_html(django_user_model):
    user = pessoa(django_user_model)
    edital()
    assert alertas.enviar(alertas.montar(Preference.objects.get(user=user))) is True
    assert len(mail.outbox) == 1
    mensagem = mail.outbox[0]
    assert mensagem.to == ["alguem@exemplo.com"]
    assert "limpeza" in mensagem.body.lower()
    assert "/oportunidades/" in mensagem.body
    assert mensagem.alternatives[0][1] == "text/html"


def test_envio_explica_por_que_apareceu(django_user_model):
    user = pessoa(django_user_model)
    edital()
    alertas.enviar(alertas.montar(Preference.objects.get(user=user)))
    assert "limpeza" in mail.outbox[0].body


def test_envio_marca_como_avisado(django_user_model):
    user = pessoa(django_user_model)
    edital()
    alertas.enviar(alertas.montar(Preference.objects.get(user=user)))
    assert Alert.objects.filter(user=user).count() == 1
    assert alertas.montar(Preference.objects.get(user=user)) is None


def test_conta_sem_email_nao_recebe(django_user_model):
    user = pessoa(django_user_model, email="")
    edital()
    assert alertas.enviar(alertas.montar(Preference.objects.get(user=user))) is False
    assert not mail.outbox


def test_falha_de_envio_nao_marca_como_avisado(django_user_model, monkeypatch):
    """Se o SMTP recusar, o edital tem que voltar na próxima rodada."""
    user = pessoa(django_user_model)
    edital()
    aviso = alertas.montar(Preference.objects.get(user=user))
    monkeypatch.setattr(
        "django.core.mail.EmailMultiAlternatives.send", lambda self, **k: 0, raising=False
    )
    assert alertas.enviar(aviso) is False
    assert Alert.objects.count() == 0


# --- rodada e comando -------------------------------------------------------


def test_rodada_ignora_quem_nao_tem_email(django_user_model):
    django_user_model.objects.create_user("mudo", email="", password="senha-longa-42")
    Preference.objects.create(user=django_user_model.objects.get(username="mudo"), market=mercado())
    edital()
    assert alertas.rodada()["pessoas"] == 0


def test_rodada_segue_depois_de_uma_falha(django_user_model, monkeypatch):
    pessoa(django_user_model)
    django_user_model.objects.create_user("outra", email="b@exemplo.com", password="senha-longa-42")
    Preference.objects.create(
        user=django_user_model.objects.get(username="outra"), market=mercado(), uf="RJ"
    )
    edital()
    chamadas = {"n": 0}

    def explode(self, **_):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            raise OSError("SMTP fora do ar")
        return 1

    monkeypatch.setattr("django.core.mail.EmailMultiAlternatives.send", explode, raising=False)
    resumo = alertas.rodada()
    assert resumo["falhas"] == 1
    assert resumo["avisos"] == 1


def test_comando_seco_nao_envia_nem_marca(django_user_model):
    pessoa(django_user_model)
    edital()
    call_command("send_alerts", "--seco")
    assert not mail.outbox
    assert Alert.objects.count() == 0


def test_comando_envia(django_user_model):
    pessoa(django_user_model)
    edital()
    call_command("send_alerts")
    assert len(mail.outbox) == 1
    assert Alert.objects.count() == 1


def test_segunda_rodada_no_mesmo_dia_nao_repete(django_user_model):
    pessoa(django_user_model)
    edital()
    call_command("send_alerts")
    call_command("send_alerts")
    assert len(mail.outbox) == 1


def test_objeto_longo_e_cortado_no_email(django_user_model):
    """Objeto de edital passa de mil caracteres; inteiro, vira muro de texto."""
    pessoa(django_user_model)
    edital(titulo="Contratação de serviços de limpeza " + "e demais exigências " * 40)
    alertas.enviar(alertas.montar(Preference.objects.get(user__username="alguem")))
    corpo = mail.outbox[0].body
    assert "…" in corpo
    assert max(len(linha) for linha in corpo.splitlines()) < 220
