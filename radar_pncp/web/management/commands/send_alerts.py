"""Envia o aviso de oportunidades novas. Feito para rodar no cron."""

from django.core.management.base import BaseCommand

from radar_pncp.web import alertas


class Command(BaseCommand):
    help = "Envia por e-mail as oportunidades ainda não avisadas a cada usuário."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limite",
            type=int,
            default=alertas.LIMITE_POR_AVISO,
            help="Máximo de oportunidades por e-mail.",
        )
        parser.add_argument(
            "--seco",
            action="store_true",
            help="Mostra o que seria enviado, sem enviar nem marcar.",
        )

    def handle(self, *args, **opcoes):
        resumo = alertas.rodada(limite=opcoes["limite"], seco=opcoes["seco"])
        prefixo = "[seco] " if opcoes["seco"] else ""
        self.stdout.write(
            f"{prefixo}{resumo['pessoas']} pessoa(s) com interesse · "
            f"{resumo['avisos']} aviso(s) · "
            f"{resumo['oportunidades']} oportunidade(s)"
        )
        if resumo["falhas"]:
            self.stdout.write(self.style.WARNING(f"{resumo['falhas']} envio(s) falharam."))
        pendentes = alertas.sem_email()
        if pendentes:
            self.stdout.write(
                self.style.WARNING(f"{pendentes} conta(s) com interesse mas sem e-mail.")
            )
