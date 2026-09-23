from __future__ import annotations

from datetime import date

from contratinho import estado
from contratinho.filtro import Achado, Licitacao


def achado(identificador: str, perfil: str = "impressos") -> Achado:
    licitacao = Licitacao(
        id=identificador,
        objeto="Impressão de cartilhas",
        orgao="Prefeitura",
        uf="SP",
        modalidade="Pregão - Eletrônico",
        modalidade_id=6,
        valor=50_000.0,
        encerramento=date(2026, 10, 1),
        publicacao=date(2026, 9, 1),
    )
    return Achado(licitacao=licitacao, perfil=perfil, termos=("impressão",))


def test_primeira_rodada_tudo_e_novo(tmp_path):
    with estado.abrir(tmp_path / "contratinho.db") as conexao:
        entradas = [achado("a"), achado("b")]
        assert estado.novos(conexao, entradas) == entradas


def test_segunda_rodada_nao_repete(tmp_path):
    banco = tmp_path / "contratinho.db"
    with estado.abrir(banco) as conexao:
        estado.marcar(conexao, [achado("a")])
    with estado.abrir(banco) as conexao:
        novos = estado.novos(conexao, [achado("a"), achado("b")])
        assert [a.licitacao.id for a in novos] == ["b"]


def test_marcar_duas_vezes_nao_estoura(tmp_path):
    with estado.abrir(tmp_path / "contratinho.db") as conexao:
        estado.marcar(conexao, [achado("a")])
        estado.marcar(conexao, [achado("a")])
        assert estado.total(conexao) == 1


def test_banco_e_criado_em_diretorio_inexistente(tmp_path):
    with estado.abrir(tmp_path / "fundo" / "contratinho.db") as conexao:
        assert estado.total(conexao) == 0


def test_lista_vazia_nao_consulta(tmp_path):
    with estado.abrir(tmp_path / "contratinho.db") as conexao:
        assert estado.ja_vistos(conexao, []) == set()
        assert estado.novos(conexao, []) == []


def test_erro_no_meio_nao_deixa_estado_pela_metade(tmp_path):
    # o cron mata o processo no meio: ou grava tudo, ou nada
    banco = tmp_path / "contratinho.db"
    try:
        with estado.abrir(banco) as conexao:
            estado.marcar(conexao, [achado("a")])
            raise RuntimeError("processo morreu")
    except RuntimeError:
        pass
    with estado.abrir(banco) as conexao:
        assert estado.total(conexao) == 0
