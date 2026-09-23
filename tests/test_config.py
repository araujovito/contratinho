from __future__ import annotations

import pytest

from contratinho import config as cfg

MINIMO = """
[[perfil]]
nome = "impressos"
termos = ["impressão"]
"""


def test_exemplo_gerado_pelo_init_e_valido():
    # se `contratinho init` cuspir um arquivo que não carrega, o projeto não anda
    configuracao = cfg.carregar_texto(cfg.EXEMPLO)
    assert [p.nome for p in configuracao.perfil] == ["impressos", "papel"]


def test_exemplo_traz_o_escopo_inicial_rj_ate_250k():
    # escopo estreito de propósito; ver o comentário no topo do arquivo gerado
    configuracao = cfg.carregar_texto(cfg.EXEMPLO)
    assert configuracao.radar.uf == ["RJ"]
    assert configuracao.radar.valor_maximo == 250_000
    assert configuracao.radar.valor_minimo is None


def test_secao_radar_e_opcional():
    configuracao = cfg.carregar_texto(MINIMO)
    assert configuracao.radar.uf == []
    assert configuracao.radar.valor_minimo is None
    assert configuracao.perfil[0].excluir == []


def test_uf_normaliza_caixa_e_espaco():
    configuracao = cfg.carregar_texto('[radar]\nuf = [" sp ", "mg"]\n' + MINIMO)
    assert configuracao.radar.uf == ["SP", "MG"]


def test_uf_inexistente_falha():
    with pytest.raises(cfg.ConfigError, match="XX"):
        cfg.carregar_texto('[radar]\nuf = ["XX"]\n' + MINIMO)


def test_modalidade_inexistente_falha():
    with pytest.raises(cfg.ConfigError, match="99"):
        cfg.carregar_texto("[radar]\nmodalidades = [99]\n" + MINIMO)


def test_faixa_de_valor_invertida_falha():
    texto = "[radar]\nvalor_minimo = 100\nvalor_maximo = 10\n" + MINIMO
    with pytest.raises(cfg.ConfigError, match="valor_minimo"):
        cfg.carregar_texto(texto)


def test_perfil_sem_termos_falha():
    with pytest.raises(cfg.ConfigError, match="termos"):
        cfg.carregar_texto('[[perfil]]\nnome = "x"\ntermos = []\n')


def test_sem_nenhum_perfil_falha():
    with pytest.raises(cfg.ConfigError, match="perfil"):
        cfg.carregar_texto('[radar]\nuf = ["SP"]\n')


def test_nome_de_perfil_repetido_falha():
    with pytest.raises(cfg.ConfigError, match="repetido"):
        cfg.carregar_texto(MINIMO + MINIMO)


def test_campo_desconhecido_falha():
    # erro de digitação em chave silenciosamente ignorado é filtro que não filtra
    with pytest.raises(cfg.ConfigError, match="valor_minimoo"):
        cfg.carregar_texto("[radar]\nvalor_minimoo = 10\n" + MINIMO)


def test_toml_malformado_falha():
    with pytest.raises(cfg.ConfigError, match="TOML inválido"):
        cfg.carregar_texto("[[perfil]\nnome =")


def test_arquivo_ausente_menciona_init(tmp_path):
    with pytest.raises(cfg.ConfigError, match="contratinho init"):
        cfg.carregar(tmp_path / "nao_existe.toml")


def test_carregar_le_do_disco(tmp_path):
    arquivo = tmp_path / "contratinho.toml"
    arquivo.write_text(MINIMO, encoding="utf-8")
    assert cfg.carregar(arquivo).perfil[0].nome == "impressos"
