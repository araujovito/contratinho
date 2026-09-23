from django.core.management.base import BaseCommand, CommandError

from radar_pncp import fonte
from radar_pncp.config import Config, Perfil
from radar_pncp.web.ingestion import publish


class Command(BaseCommand):
    help = "Consulta PNCP uma vez e atualiza o catálogo compartilhado."

    def add_arguments(self, parser):
        parser.add_argument("--dias", type=int, default=30)

    def handle(self, *args, **options):
        days = options["dias"]
        if not 1 <= days <= 365:
            raise CommandError("--dias deve estar entre 1 e 365.")
        config = Config(perfil=[Perfil(nome="coleta", termos=["coleta"])])
        try:
            items = fonte.buscar(config, dias=days)
        except Exception as exc:
            raise CommandError("Falha ao consultar PNCP; catálogo anterior preservado.") from exc
        count = publish(items)
        self.stdout.write(self.style.SUCCESS(f"{count} contratações processadas."))
