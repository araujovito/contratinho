from django.contrib.auth import views as auth
from django.urls import path

from . import admin_views, views

urlpatterns = [
    path("admin/", admin_views.dashboard, name="admin_dashboard"),
    path("admin/mercados/", admin_views.markets, name="admin_markets"),
    path("admin/mercados/novo/", admin_views.market_edit, name="admin_market_create"),
    path(
        "admin/mercados/<int:pk>/",
        admin_views.market_edit,
        name="admin_market_edit",
    ),
    path("admin/oportunidades/", admin_views.opportunities, name="admin_opportunities"),
    path(
        "admin/oportunidades/nova/",
        admin_views.opportunity_edit,
        name="admin_opportunity_create",
    ),
    path(
        "admin/oportunidades/<int:pk>/",
        admin_views.opportunity_edit,
        name="admin_opportunity_edit",
    ),
    path("admin/usuarios/", admin_views.users, name="admin_users"),
    path("", views.home, name="home"),
    path("conta/criar/", views.signup, name="signup"),
    path("conta/entrar/", auth.LoginView.as_view(template_name="radar/login.html"), name="login"),
    path("conta/sair/", auth.LogoutView.as_view(), name="logout"),
    path("interesses/", views.preferences, name="preferences"),
    path("oportunidades/", views.opportunities, name="opportunities"),
    path("oportunidades/<int:pk>/", views.detail, name="detail"),
    path("oportunidades/<int:pk>/acompanhar/", views.follow, name="follow"),
    path("acompanhando/", views.following, name="following"),
    path("acompanhando/<int:pk>/etapa/", views.update_follow, name="update_follow"),
    path("acompanhando/<int:pk>/remover/", views.unfollow, name="unfollow"),
]
