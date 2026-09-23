"""Memória do radar: o que já foi avisado.

SQLite em arquivo único. Sem ORM — são duas queries.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from contratinho.filtro import Achado

ESQUEMA = """
CREATE TABLE IF NOT EXISTS visto (
    id          TEXT PRIMARY KEY,
    perfil      TEXT NOT NULL,
    objeto      TEXT NOT NULL,
    visto_em    TEXT NOT NULL
);
"""


@contextmanager
def abrir(caminho: Path):
    """Conexão com o esquema garantido. Commit no fim, rollback em erro."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho)
    try:
        conexao.execute("PRAGMA journal_mode=WAL")
        conexao.executescript(ESQUEMA)
        yield conexao
        conexao.commit()
    except BaseException:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def ja_vistos(conexao: sqlite3.Connection, ids: Iterable[str]) -> set[str]:
    ids = list(ids)
    if not ids:
        return set()
    marcadores = ",".join("?" * len(ids))
    cursor = conexao.execute(f"SELECT id FROM visto WHERE id IN ({marcadores})", ids)
    return {linha[0] for linha in cursor}


def novos(conexao: sqlite3.Connection, achados: list[Achado]) -> list[Achado]:
    """Filtra os achados que ainda não foram avisados. Não grava nada."""
    vistos = ja_vistos(conexao, (a.licitacao.id for a in achados))
    return [a for a in achados if a.licitacao.id not in vistos]


def marcar(conexao: sqlite3.Connection, achados: list[Achado]) -> None:
    """Grava os achados como avisados.

    Só é chamado depois que a saída foi impressa: se o processo morrer antes,
    o aviso se repete na próxima rodada — melhor repetir do que perder.
    """
    agora = datetime.now().isoformat(timespec="seconds")
    conexao.executemany(
        "INSERT OR IGNORE INTO visto (id, perfil, objeto, visto_em) VALUES (?, ?, ?, ?)",
        [(a.licitacao.id, a.perfil, a.licitacao.objeto[:500], agora) for a in achados],
    )


def total(conexao: sqlite3.Connection) -> int:
    return conexao.execute("SELECT COUNT(*) FROM visto").fetchone()[0]
