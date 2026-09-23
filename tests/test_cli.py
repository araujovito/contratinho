from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from exemplos import CONFIG_TESTE
from typer.testing import CliRunner

from contratinho import config as cfg
from contratinho import fonte
from contratinho.cli import app
from contratinho.filtro import Licitacao

runner = CliRunner()
FIXTURE = Path(__file__).parent / "fixtures" / "contratacoes_proposta.json"


@pytest.fixture
def pncp_falso(monkeypatch):
    """`contratinho check` sem rede: devolve a fixture já traduzida."""
    from pypncp.models import Contratacao

    bruto = json.loads(FIXTURE.read_text(encoding="utf-8"))["data"]
    licitacoes = [fonte.para_licitacao(Contratacao.model_validate(item)) for item in bruto]
    monkeypatch.setattr(fonte, "buscar", lambda *a, **k: licitacoes)
    return licitacoes


def test_init_cria_config_valido(tmp_path):
    destino = tmp_path / "contratinho.toml"
    resultado = runner.invoke(app, ["init", "--config", str(destino)])
    assert resultado.exit_code == 0
    assert cfg.carregar(destino).perfil  # o que foi gerado carrega


def test_init_nao_sobrescreve_sem_force(tmp_path):
    destino = tmp_path / "contratinho.toml"
    destino.write_text("# meu arquivo\n", encoding="utf-8")
    resultado = runner.invoke(app, ["init", "--config", str(destino)])
    assert resultado.exit_code == 1
    assert destino.read_text(encoding="utf-8") == "# meu arquivo\n"

    forcado = runner.invoke(app, ["init", "--config", str(destino), "--force"])
    assert forcado.exit_code == 0
    assert "perfil" in destino.read_text(encoding="utf-8")


def test_check_sem_config_orienta_a_rodar_init(tmp_path):
    resultado = runner.invoke(app, ["check", "--config", str(tmp_path / "nada.toml")])
    assert resultado.exit_code == 1
    assert "contratinho init" in resultado.output


def test_check_imprime_e_nao_repete(tmp_path, pncp_falso):
    config = tmp_path / "contratinho.toml"
    config.write_text(CONFIG_TESTE, encoding="utf-8")
    banco = tmp_path / "contratinho.db"
    argumentos = ["check", "--config", str(config), "--db", str(banco)]

    primeira = runner.invoke(app, argumentos)
    assert primeira.exit_code == 0
    assert "cartilha" in primeira.output.lower()

    segunda = runner.invoke(app, argumentos)
    assert segunda.exit_code == 0
    assert "Nada novo" in segunda.output


def test_seco_nao_grava_estado(tmp_path, pncp_falso):
    config = tmp_path / "contratinho.toml"
    config.write_text(CONFIG_TESTE, encoding="utf-8")
    banco = tmp_path / "contratinho.db"
    argumentos = ["check", "--config", str(config), "--db", str(banco), "--seco"]

    runner.invoke(app, argumentos)
    segunda = runner.invoke(app, argumentos)
    assert "Nada novo" not in segunda.output


def test_falha_de_rede_sai_com_codigo_2(tmp_path, monkeypatch):
    config = tmp_path / "contratinho.toml"
    config.write_text(CONFIG_TESTE, encoding="utf-8")

    def explodir(*_a, **_k):
        raise TimeoutError("PNCP fora do ar")

    monkeypatch.setattr(fonte, "buscar", explodir)
    resultado = runner.invoke(app, ["check", "--config", str(config), "--db", str(tmp_path / "d")])
    assert resultado.exit_code == 2
    assert "PNCP" in resultado.output


def test_config_invalido_sai_com_codigo_1(tmp_path):
    config = tmp_path / "contratinho.toml"
    config.write_text('[radar]\nuf = ["XX"]\n[[perfil]]\nnome="a"\ntermos=["b"]\n', "utf-8")
    resultado = runner.invoke(app, ["check", "--config", str(config)])
    assert resultado.exit_code == 1


def test_version():
    resultado = runner.invoke(app, ["version"])
    assert resultado.exit_code == 0
    assert resultado.output.strip()


def test_moeda_no_formato_brasileiro():
    from contratinho.saida import moeda

    assert moeda(184500.0) == "R$ 184.500,00"
    assert moeda(None) == "—"


def test_saida_nao_quebra_sem_uf_nem_url():
    from contratinho.filtro import Achado
    from contratinho.saida import imprimir_achados

    licitacao = Licitacao(
        id="x",
        objeto="Impressão",
        orgao="Órgão",
        uf=None,
        modalidade="",
        modalidade_id=None,
        valor=None,
        encerramento=None,
        publicacao=date(2026, 1, 1),
    )
    imprimir_achados([Achado(licitacao, "impressos", ("impressão",))], janela_dias=30)
