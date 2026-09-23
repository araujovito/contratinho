"""Interface de linha de comando.

Dois comandos: `radar init` cria o arquivo de regras, `radar check` roda uma
vez. Agendar é problema do cron ou do Agendador de Tarefas — ver README.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from radar_pncp import __version__, estado, filtro, fonte, saida
from radar_pncp import config as cfg

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Radar de licitações do PNCP: avisa só o que é novo e casa com o seu ramo.",
)

CONFIG_PADRAO = Path("radar.toml")
BANCO_PADRAO = Path("radar.db")


@app.command()
def init(
    caminho: Annotated[
        Path, typer.Option("--config", "-c", help="Onde gravar o arquivo.")
    ] = CONFIG_PADRAO,
    forcar: Annotated[
        bool, typer.Option("--force", "-f", help="Sobrescreve se já existir.")
    ] = False,
) -> None:
    """Gera um radar.toml de exemplo, comentado."""
    if caminho.exists() and not forcar:
        saida.erro(f"{caminho} já existe. Use --force para sobrescrever.")
        raise typer.Exit(code=1)
    caminho.write_text(cfg.EXEMPLO, encoding="utf-8")
    saida.console.print(f"[green]criado[/green] {caminho}")
    saida.console.print("[dim]Edite os perfis e rode `radar check`.[/dim]")


@app.command()
def check(
    caminho: Annotated[
        Path, typer.Option("--config", "-c", help="Arquivo de regras.")
    ] = CONFIG_PADRAO,
    banco: Annotated[Path, typer.Option("--db", help="Banco de estado (SQLite).")] = BANCO_PADRAO,
    dias: Annotated[
        int,
        typer.Option(
            "--dias",
            "-d",
            min=1,
            max=365,
            help="Considera propostas que encerram nos próximos N dias.",
        ),
    ] = fonte.JANELA_PADRAO_DIAS,
    tudo: Annotated[
        bool,
        typer.Option("--tudo", help="Mostra também o que já foi avisado (não grava estado)."),
    ] = False,
    seco: Annotated[bool, typer.Option("--seco", help="Imprime sem marcar como avisado.")] = False,
) -> None:
    """Consulta o PNCP uma vez e imprime as licitações novas."""
    try:
        configuracao = cfg.carregar(caminho)
    except cfg.ConfigError as problema:
        saida.erro(str(problema))
        raise typer.Exit(code=1) from problema

    with saida.console.status("consultando o PNCP…"):
        try:
            licitacoes = fonte.buscar(configuracao, dias=dias)
        except Exception as problema:  # rede, timeout, 5xx do PNCP
            saida.erro(f"falha ao consultar o PNCP: {problema}")
            raise typer.Exit(code=2) from problema

    achados = filtro.filtrar(licitacoes, configuracao)

    if tudo:
        saida.imprimir_achados(achados, janela_dias=dias)
        saida.imprimir_resumo(baixadas=len(licitacoes), casaram=len(achados), novas=len(achados))
        return

    with estado.abrir(banco) as conexao:
        ineditos = estado.novos(conexao, achados)
        saida.imprimir_achados(ineditos, janela_dias=dias)
        saida.imprimir_resumo(baixadas=len(licitacoes), casaram=len(achados), novas=len(ineditos))
        if not seco:
            estado.marcar(conexao, ineditos)


@app.command()
def version() -> None:
    """Mostra a versão instalada."""
    saida.console.print(__version__)


if __name__ == "__main__":
    app()
