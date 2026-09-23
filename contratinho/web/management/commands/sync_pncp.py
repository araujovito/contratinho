from django.core.management.base import BaseCommand, CommandError

from contratinho import fonte
from contratinho.config import Config, Perfil
from contratinho.web.ingestion import publish
from contratinho.web.models import Market
from contratinho.web.portal import buscar_mercados


class Command(BaseCommand):
    help = "Consulta PNCP uma vez e atualiza o catálogo compartilhado."

    def add_arguments(self, parser):
        parser.add_argument("--dias", type=int, default=30)
        parser.add_argument(
            "--fonte",
            choices=["portal", "consulta"],
            default="portal",
            help="portal usa a busca pública; consulta preserva a integração anterior.",
        )

    def handle(self, *args, **options):
        days = options["dias"]
        if not 1 <= days <= 365:
            raise CommandError("--dias deve estar entre 1 e 365.")
        try:
            if options["fonte"] == "portal":
                items = buscar_mercados(list(Market.objects.all()))
            else:
                config = Config(perfil=[Perfil(nome="coleta", termos=["coleta"])])
                items = fonte.buscar(config, dias=days)
        except Exception as exc:
            raise CommandError("Falha ao consultar PNCP; catálogo anterior preservado.") from exc
        count = publish(items)
        self.stdout.write(self.style.SUCCESS(f"{count} contratações processadas."))
