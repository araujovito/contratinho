from django.conf import settings
from django.contrib.auth import get_user_model, login


class LocalAdminMiddleware:
    """Abre o admin sem credenciais somente em desenvolvimento local."""

    local_addresses = {"127.0.0.1", "::1"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_login(request):
            user, _ = get_user_model().objects.get_or_create(
                username="admin-local",
                defaults={"is_staff": True, "is_superuser": True, "is_active": True},
            )
            if not user.is_staff or not user.is_superuser or not user.is_active:
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.save(update_fields=["is_staff", "is_superuser", "is_active"])
            if user.has_usable_password():
                user.set_unusable_password()
                user.save(update_fields=["password"])
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return self.get_response(request)

    # Cabeçalhos que só existem quando há proxy na frente. Atrás de um nginx no
    # mesmo host, REMOTE_ADDR vira 127.0.0.1 para **todo** visitante: sozinho,
    # ele deixaria de provar que o acesso é local e abriria o admin para a
    # internet. A presença de qualquer um destes derruba o atalho.
    proxy_headers = (
        "HTTP_X_FORWARDED_FOR",
        "HTTP_X_FORWARDED_HOST",
        "HTTP_X_REAL_IP",
        "HTTP_FORWARDED",
    )

    def _behind_proxy(self, request):
        return any(request.META.get(header) for header in self.proxy_headers)

    def _should_login(self, request):
        return (
            settings.DEBUG
            and request.path.startswith("/admin/")
            and request.META.get("REMOTE_ADDR") in self.local_addresses
            and not self._behind_proxy(request)
            and not (request.user.is_authenticated and request.user.is_staff)
        )
