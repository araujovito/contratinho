import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parents[2]
DEBUG = os.environ.get("CONTRATINHO_DEBUG", "0") == "1"
SECRET_KEY = os.environ.get("CONTRATINHO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "Defina CONTRATINHO_SECRET_KEY ou CONTRATINHO_DEBUG=1 para desenvolvimento."
        )
    SECRET_KEY = "development-only-never-use-in-production-contratinho"
ALLOWED_HOSTS = os.environ.get("CONTRATINHO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "contratinho.web",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "contratinho.web.middleware.LocalAdminMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "contratinho.web.urls"
WSGI_APPLICATION = "contratinho.web.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'web.sqlite3'}", conn_max_age=60
    )
}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# --- Envio de e-mail -------------------------------------------------------
# Sem CONTRATINHO_SMTP_HOST o Django imprime a mensagem no terminal, que é o que se
# quer em desenvolvimento: dá para ler o alerta inteiro sem configurar nada.
EMAIL_HOST = os.environ.get("CONTRATINHO_SMTP_HOST", "")
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = int(os.environ.get("CONTRATINHO_SMTP_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("CONTRATINHO_SMTP_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("CONTRATINHO_SMTP_PASSWORD", "")
    EMAIL_USE_TLS = os.environ.get("CONTRATINHO_SMTP_TLS", "1") == "1"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get(
    "CONTRATINHO_FROM_EMAIL", "Contratinho <nao-responda@localhost>"
)
# Endereço público do site, para os links do e-mail: a mensagem é lida fora do
# navegador, então caminho relativo não serve.
CONTRATINHO_SITE_URL = os.environ.get("CONTRATINHO_SITE_URL", "http://127.0.0.1:8000").rstrip("/")

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "opportunities"
LOGOUT_REDIRECT_URL = "home"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
