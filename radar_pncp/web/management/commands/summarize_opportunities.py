import os

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from radar_pncp.web.ai import source_hash, summarize
from radar_pncp.web.models import Opportunity


class Command(BaseCommand):
    help = "Gera explicações em linguagem simples para oportunidades do PNCP."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        if not os.getenv("OPENAI_API_KEY"):
            raise CommandError("Defina OPENAI_API_KEY para gerar os resumos.")
        limit = options["limit"]
        if not 1 <= limit <= 500:
            raise CommandError("--limit deve estar entre 1 e 500.")

        processed = 0
        queryset = Opportunity.objects.order_by("-fetched_at")
        for item in queryset.iterator():
            fingerprint = source_hash(item)
            if not options["force"] and item.summary_source_hash == fingerprint:
                continue
            result = summarize(item)
            item.plain_summary = result.summary
            item.key_points = result.key_points[:5]
            item.cautions = result.cautions[:3]
            item.summary_model = os.getenv("RADAR_AI_MODEL", "gpt-4o-mini")
            item.summary_source_hash = fingerprint
            item.summarized_at = timezone.now()
            item.save(
                update_fields=[
                    "plain_summary",
                    "key_points",
                    "cautions",
                    "summary_model",
                    "summary_source_hash",
                    "summarized_at",
                ]
            )
            processed += 1
            if processed >= limit:
                break
        self.stdout.write(self.style.SUCCESS(f"{processed} oportunidades resumidas."))
