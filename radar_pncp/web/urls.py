from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
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
