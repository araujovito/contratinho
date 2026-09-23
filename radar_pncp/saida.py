"""Formatação para o terminal.

Único canal de notificação da v0.1. Fica isolado aqui para que acrescentar
e-mail ou Telegram depois seja acrescentar um módulo, não mexer no resto.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from radar_pncp.filtro import Achado

console = Console()


def moeda(valor: float | None) -> str:
    if valor is None:
        return "—"
    inteiro, centavos = f"{valor:,.2f}".split(".")
    return f"R$ {inteiro.replace(',', '.')},{centavos}"


def _resumir(texto: str, limite: int = 110) -> str:
    texto = " ".join(texto.split())
    return texto if len(texto) <= limite else texto[: limite - 1].rstrip() + "…"


def imprimir_achados(achados: list[Achado], *, janela_dias: int) -> None:
    if not achados:
        console.print("[dim]Nada novo. As licitações já avisadas não repetem.[/dim]")
        return

    titulo = (
        f"{len(achados)} licitação(ões) nova(s) — propostas abertas nos próximos {janela_dias} dias"
    )
    tabela = Table(
        title=titulo,
        title_style="bold",
        header_style="bold",
        show_lines=True,
        expand=True,
    )
    tabela.add_column("Perfil", style="cyan", no_wrap=True)
    tabela.add_column("UF", width=3, justify="center")
    tabela.add_column("Objeto", overflow="fold")
    tabela.add_column("Valor", justify="right", no_wrap=True)

    for achado in achados:
        licitacao = achado.licitacao
        objeto = Text(_resumir(licitacao.objeto))
        objeto.append(f"\n{licitacao.orgao} · {licitacao.modalidade}", style="dim")
        objeto.append(f"\ntermos: {', '.join(achado.termos)}", style="dim italic")
        if licitacao.url:
            objeto.append(f"\n{licitacao.url}", style="blue dim")
        tabela.add_row(achado.perfil, licitacao.uf or "—", objeto, moeda(licitacao.valor))

    console.print(tabela)


def imprimir_resumo(*, baixadas: int, casaram: int, novas: int) -> None:
    console.print(
        f"[dim]{baixadas} contratações consultadas · "
        f"{casaram} casaram com algum perfil · {novas} ainda não avisadas[/dim]"
    )


def erro(mensagem: str) -> None:
    console.print(Panel(mensagem, title="erro", border_style="red", title_align="left"))
