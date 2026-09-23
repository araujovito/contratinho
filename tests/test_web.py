from dataclasses import replace
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from radar_pncp.filtro import Licitacao
from radar_pncp.web.ingestion import publish
from radar_pncp.web.models import Follow, Market, Opportunity, Preference
from radar_pncp.web.portal import buscar_mercados

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(username="fornecedor", password="senha-longa-de-teste-123")


@pytest.fixture
def item():
    return Licitacao(
        id="123-2026-1",
        objeto="Impressão de cartilhas",
        orgao="Órgão exemplo",
        uf="RJ",
        modalidade="Pregão",
        modalidade_id=6,
        valor=1500,
        encerramento=None,
        publicacao=None,
        url="https://pncp.gov.br/app/editais/123/2026/1",
    )


def test_signup_onboarding_and_private_session(client):
    response = client.post(
        reverse("signup"),
        {
            "username": "novo",
            "password1": "senha-segura-e-comprida-42",
            "password2": "senha-segura-e-comprida-42",
        },
    )
    assert response.status_code == 302
    assert response.url == reverse("preferences")
    assert User.objects.get(username="novo").check_password("senha-segura-e-comprida-42")
    market = Market.objects.get(slug="graficos")
    response = client.post(reverse("preferences"), {"market": market.pk, "uf": "RJ"})
    assert response.url == reverse("opportunities")
    assert Preference.objects.get(user__username="novo").uf == "RJ"
    assert client.get(reverse("opportunities")).status_code == 200


def test_requires_login(client):
    for name in ["preferences", "opportunities", "following"]:
        assert client.get(reverse(name)).status_code == 302


@override_settings(DEBUG=True)
def test_local_admin_opens_without_credentials(client):
    response = client.get(reverse("admin_dashboard"))
    assert response.status_code == 200
    assert response.wsgi_request.user.username == "admin-local"
    assert not response.wsgi_request.user.has_usable_password()
    assert reverse("admin_markets") in response.content.decode()


@override_settings(DEBUG=False)
def test_admin_requires_staff_user_outside_local_development(client, user):
    client.force_login(user)
    response = client.get(reverse("admin_dashboard"))
    assert response.status_code == 302

    user.is_staff = True
    user.is_superuser = True
    user.save(update_fields=["is_staff", "is_superuser"])
    response = client.get(reverse("admin_dashboard"))
    assert response.status_code == 200
    assert reverse("admin_markets") in response.content.decode()


@override_settings(DEBUG=True)
def test_management_market_editor_uses_plain_text_terms(client):
    market = Market.objects.get(slug="graficos")
    response = client.get(reverse("admin_market_edit", args=[market.pk]))
    assert response.status_code == 200
    assert "impressão, gráfica" in response.content.decode()

    response = client.post(
        reverse("admin_market_edit", args=[market.pk]),
        {
            "name": "Gráfica rápida",
            "slug": "graficos",
            "terms": "impressão, banner, cartão",
            "exclusions": "toner, cartucho",
        },
    )
    assert response.status_code == 302
    market.refresh_from_db()
    assert market.name == "Gráfica rápida"
    assert market.terms == ["impressão", "banner", "cartão"]


@override_settings(DEBUG=True)
def test_management_opportunity_uses_checkboxes_for_markets(client, item):
    publish([item])
    opportunity = Opportunity.objects.get()
    response = client.get(reverse("admin_opportunity_edit", args=[opportunity.pk]))
    body = response.content.decode()
    assert response.status_code == 200
    assert 'type="checkbox"' in body
    assert "selector-available" not in body
    assert "O que o órgão precisa contratar?" in body
    assert "opportunity-object-input" in body


@override_settings(DEBUG=True)
def test_market_card_opens_only_its_opportunities(client, item):
    publish(
        [
            item,
            replace(item, id="informatica-1", objeto="Suporte técnico de informática"),
        ]
    )
    market = Market.objects.get(slug="graficos")
    market_page = client.get(reverse("admin_markets"))
    expected_url = f"{reverse('admin_opportunities')}?mercado={market.slug}"
    assert expected_url in market_page.content.decode()

    response = client.get(reverse("admin_opportunities"), {"mercado": market.slug})
    assert response.status_code == 200
    assert [opportunity.pncp_id for opportunity in response.context["page"]] == [item.id]
    assert response.context["selected_market"] == market


@override_settings(DEBUG=True)
def test_market_dashboard_filters_rj_and_value_ceiling(client, item):
    item = replace(
        item,
        publicacao=date(2026, 9, 15),
        abertura=date(2026, 9, 16),
        encerramento=date(2026, 10, 1),
    )
    publish(
        [
            item,
            replace(item, id="high-value", valor=90000),
            replace(item, id="other-state", uf="SP", valor=1000),
            replace(item, id="unknown-value", valor=None),
        ]
    )
    response = client.get(
        reverse("admin_opportunities"),
        {"mercado": "graficos", "valor_maximo": "5000"},
    )
    assert response.status_code == 200
    assert {opportunity.pncp_id for opportunity in response.context["page"]} == {
        item.id,
        "unknown-value",
    }
    assert response.context["value_ceiling"] == 5000
    assert response.context["market_stats"] == {"total_rj": 3, "without_value": 1}
    body = response.content.decode()
    assert "Serviços gráficos no RJ" in body
    assert "Qual é o valor máximo" in body
    assert "Até R$ 50 mil" in body
    assert "Até R$ 500 mil" in body
    assert "15/09/2026" in body
    assert "16/09/2026" in body
    assert "01/10/2026" in body
    assert "Abrir edital" in body
    assert "Pesquisar no PNCP" in body
    assert "status=recebendo_proposta" in body
    assert "ufs=RJ" in body


def test_catalog_filter_follow_and_stage(client, user, item):
    publish(
        [
            item,
            replace(item, id="other-state", uf="SP"),
            replace(item, id="expired", encerramento=timezone.localdate() - timedelta(days=1)),
        ]
    )
    Preference.objects.create(user=user, market=Market.objects.get(slug="graficos"), uf="RJ")
    client.force_login(user)
    response = client.get(reverse("opportunities"))
    assert [i.pncp_id for i in response.context["page"]] == [item.id]
    body = response.content.decode()
    assert "Entender oportunidade" in body
    assert "Por que apareceu" in body
    assert "Ver no PNCP" in body
    opportunity = Opportunity.objects.get(pncp_id=item.id)
    detail_response = client.get(reverse("detail", args=[opportunity.pk]))
    assert detail_response.status_code == 200
    detail_body = detail_response.content.decode()
    assert "RESUMO DA OPORTUNIDADE" in detail_body
    assert "Objeto publicado pelo órgão" in detail_body
    assert "Calcule se vale a pena" in detail_body
    url = reverse("follow", args=[opportunity.pk])
    assert client.get(url).status_code == 405
    client.post(url)
    client.post(url)
    assert Follow.objects.filter(user=user).count() == 1
    follow = Follow.objects.get(user=user)
    client.post(reverse("update_follow", args=[follow.pk]), {"stage": "preparing"})
    follow.refresh_from_db()
    assert follow.stage == "preparing"
    assert client.get(reverse("following")).status_code == 200


def test_other_users_cannot_read_change_or_delete_follow(client, user, item):
    publish([item])
    owner = User.objects.create_user(username="dono")
    follow = Follow.objects.create(user=owner, opportunity=Opportunity.objects.get())
    client.force_login(user)
    assert not client.get(reverse("following")).context["page"].object_list
    for name in ["update_follow", "unfollow"]:
        assert (
            client.post(reverse(name, args=[follow.pk]), {"stage": "archived"}).status_code == 404
        )
    follow.refresh_from_db()
    assert follow.stage == "interested"


def test_csrf_enforced(user, item):
    publish([item])
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    assert client.post(reverse("follow", args=[Opportunity.objects.get().pk])).status_code == 403
    assert client.post(reverse("preferences"), {}).status_code == 403


def test_ingestion_updates_without_losing_follow(user, item):
    publish([item])
    original = Opportunity.objects.get()
    Follow.objects.create(user=user, opportunity=original)
    publish([replace(item, objeto="Aquisição de computadores", valor=None)])
    assert Opportunity.objects.count() == 1
    original.refresh_from_db()
    assert original.value is None
    assert list(original.markets.values_list("slug", flat=True)) == ["informatica"]
    assert Follow.objects.get().opportunity_id == original.pk


def test_failed_batch_rolls_back(item):
    publish([item])
    with pytest.raises(ValueError):
        publish([replace(item, objeto="alteração"), replace(item, id="None-None-None")])
    assert Opportunity.objects.get().title == item.objeto


def test_failed_network_keeps_catalog(item):
    publish([item])
    with patch("radar_pncp.fonte.buscar", side_effect=TimeoutError), pytest.raises(CommandError):
        call_command("sync_pncp", fonte="consulta")
    assert Opportunity.objects.count() == 1


def test_portal_search_maps_dates_value_and_official_url():
    payload = {
        "total": 1,
        "items": [
            {
                "numero_controle_pncp": "12345678000190-1-000123/2026",
                "description": "Serviço de limpeza predial",
                "orgao_nome": "Órgão exemplo",
                "orgao_cnpj": "12345678000190",
                "uf": "RJ",
                "ano": "2026",
                "numero_sequencial": "123",
                "modalidade_licitacao_id": "6",
                "modalidade_licitacao_nome": "Pregão - Eletrônico",
                "valor_global": 42000.5,
                "data_publicacao_pncp": "2026-09-15T09:00:00",
                "data_inicio_vigencia": "2026-09-16T08:00:00",
                "data_fim_vigencia": "2026-10-01T18:00:00",
            }
        ],
    }

    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return payload

    class Client:
        def __init__(self):
            self.requests = []

        def get(self, url, params):
            self.requests.append((url, params))
            return Response()

    client = Client()
    market = Market(name="Limpeza", slug="limpeza", terms=["limpeza"])
    results = buscar_mercados([market], client=client, pause=0)

    assert len(results) == 1
    result = results[0]
    assert result.valor == 42000.5
    assert result.publicacao == date(2026, 9, 15)
    assert result.abertura == date(2026, 9, 16)
    assert result.encerramento == date(2026, 10, 1)
    assert result.url == "https://pncp.gov.br/app/editais/12345678000190/2026/123"
    assert client.requests[0][1]["ufs"] == "RJ"
    assert client.requests[0][1]["status"] == "recebendo_proposta"


def test_untrusted_url_not_published(item):
    publish([replace(item, url="javascript:alert(1)")])
    assert Opportunity.objects.get().official_url == ""


def test_readable_object_preserves_official_title(item):
    publish([replace(item, objeto="[Portal de Compras Públicas] - COMPRA DE MATERIAL DE LIMPEZA")])
    opportunity = Opportunity.objects.get()
    assert opportunity.readable_object == "Compra de material de limpeza"
    assert opportunity.title.startswith("[Portal de Compras Públicas]")


def test_ai_summary_is_shown_with_original_and_official_link(client, user, item):
    publish([item])
    opportunity = Opportunity.objects.get()
    opportunity.plain_summary = "O órgão quer contratar impressão de cartilhas."
    opportunity.key_points = ["Entrega no Rio de Janeiro"]
    opportunity.cautions = ["Confira a quantidade no edital"]
    opportunity.save()
    client.force_login(user)
    body = client.get(reverse("detail", args=[opportunity.pk])).content.decode()
    assert "EM LINGUAGEM SIMPLES" in body
    assert "Entrega no Rio de Janeiro" in body
    assert "Objeto publicado pelo órgão" in body
    assert "Ler edital completo no PNCP" in body


def test_summary_command_persists_structured_result(item, monkeypatch):
    publish([item])
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    result = SimpleNamespace(
        summary="Impressão de cartilhas para o órgão.",
        key_points=["Serviço gráfico"],
        cautions=["Confira as quantidades"],
    )
    with patch(
        "radar_pncp.web.management.commands.summarize_opportunities.summarize", return_value=result
    ):
        call_command("summarize_opportunities", limit=1)
    opportunity = Opportunity.objects.get()
    assert opportunity.plain_summary == result.summary
    assert opportunity.key_points == result.key_points
    assert opportunity.summary_source_hash


def test_invalid_preferences_and_stage(client, user, item):
    client.force_login(user)
    response = client.post(reverse("preferences"), {"market": 999999, "uf": "XX"})
    assert response.status_code == 200
    assert not Preference.objects.exists()
    publish([item])
    follow = Follow.objects.create(user=user, opportunity=Opportunity.objects.get())
    client.post(reverse("update_follow", args=[follow.pk]), {"stage": "invented"})
    follow.refresh_from_db()
    assert follow.stage == "interested"


def test_pagination_and_escaping(client, user, item):
    publish(
        [replace(item, id=str(i), objeto="Impressão <script>alert(1)</script>") for i in range(21)]
    )
    Preference.objects.create(user=user, market=Market.objects.get(slug="graficos"))
    client.force_login(user)
    first = client.get(reverse("opportunities"))
    assert len(first.context["page"]) == 20
    assert b"<script>" not in first.content
    assert len(client.get(reverse("opportunities"), {"page": 2}).context["page"]) == 1
