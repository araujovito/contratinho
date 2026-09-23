"""Carga e validação do radar.toml.

Módulo puro: não abre rede nem banco. Recebe texto TOML (ou um caminho) e
devolve objetos validados — é o que permite testar o parsing sem mock.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator

UFS = {
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
}

# Códigos da tabela de modalidade do PNCP (Lei 14.133). Só os usados na prática;
# a lista completa está na documentação da API de consulta.
MODALIDADES = {
    1: "Leilão - Eletrônico",
    2: "Diálogo Competitivo",
    3: "Concurso",
    4: "Concorrência - Eletrônica",
    5: "Concorrência - Presencial",
    6: "Pregão - Eletrônico",
    7: "Pregão - Presencial",
    8: "Dispensa de Licitação",
    9: "Inexigibilidade",
    10: "Manifestação de Interesse",
    11: "Pré-qualificação",
    12: "Credenciamento",
    13: "Leilão - Presencial",
}


class ConfigError(Exception):
    """radar.toml ausente, malformado ou com valores inválidos."""


class RadarSecao(BaseModel):
    """Filtros globais, aplicados antes dos perfis."""

    model_config = {"extra": "forbid"}

    uf: list[str] = Field(default_factory=list)
    valor_minimo: float | None = None
    valor_maximo: float | None = None
    modalidades: list[int] = Field(default_factory=list)

    @field_validator("uf")
    @classmethod
    def _uf_valida(cls, valor: list[str]) -> list[str]:
        normalizadas = [uf.strip().upper() for uf in valor]
        desconhecidas = sorted(set(normalizadas) - UFS)
        if desconhecidas:
            raise ValueError(f"UF inexistente: {', '.join(desconhecidas)}")
        return normalizadas

    @field_validator("modalidades")
    @classmethod
    def _modalidade_valida(cls, valor: list[int]) -> list[int]:
        desconhecidas = sorted(set(valor) - set(MODALIDADES))
        if desconhecidas:
            conhecidas = ", ".join(f"{k}={v}" for k, v in MODALIDADES.items())
            raise ValueError(
                f"código de modalidade inexistente: {desconhecidas}. Válidos: {conhecidas}"
            )
        return valor


class Perfil(BaseModel):
    """Um ramo de atuação: o que procurar e o que descartar."""

    model_config = {"extra": "forbid"}

    nome: str
    termos: list[str] = Field(min_length=1)
    excluir: list[str] = Field(default_factory=list)


class Config(BaseModel):
    model_config = {"extra": "forbid"}

    radar: RadarSecao = Field(default_factory=RadarSecao)
    perfil: list[Perfil] = Field(min_length=1)

    @field_validator("perfil")
    @classmethod
    def _nomes_unicos(cls, valor: list[Perfil]) -> list[Perfil]:
        nomes = [p.nome for p in valor]
        repetidos = sorted({n for n in nomes if nomes.count(n) > 1})
        if repetidos:
            raise ValueError(f"nome de perfil repetido: {', '.join(repetidos)}")
        return valor


def carregar_texto(texto: str) -> Config:
    """Valida um radar.toml já lido. É aqui que os testes entram."""
    try:
        dados = tomllib.loads(texto)
    except tomllib.TOMLDecodeError as erro:
        raise ConfigError(f"TOML inválido: {erro}") from erro
    try:
        config = Config.model_validate(dados)
    except ValidationError as erro:
        raise ConfigError(_mensagem(erro)) from erro
    if (
        config.radar.valor_minimo is not None
        and config.radar.valor_maximo is not None
        and config.radar.valor_minimo > config.radar.valor_maximo
    ):
        raise ConfigError("valor_minimo é maior que valor_maximo")
    return config


def carregar(caminho: Path) -> Config:
    if not caminho.exists():
        raise ConfigError(f"{caminho} não encontrado. Rode `radar init` para criar um exemplo.")
    return carregar_texto(caminho.read_text(encoding="utf-8"))


def _mensagem(erro: ValidationError) -> str:
    linhas = []
    for item in erro.errors():
        campo = ".".join(str(parte) for parte in item["loc"]) or "(raiz)"
        linhas.append(f"{campo}: {item['msg']}")
    return "; ".join(linhas)


EXEMPLO = """\
# Escopo inicial: contratos de até R$ 250 mil no Rio de Janeiro.
# Comece estreito. Ampliar depois é acrescentar UF ou subir o teto; começar
# largo é receber cem avisos no primeiro dia e parar de ler todos eles.
[radar]
uf = ["RJ"]
valor_maximo = 250000
# valor_minimo = 10000   # sem mínimo, edital sem valor estimado também aparece
# modalidades = [6, 8]   # 6 = Pregão Eletrônico, 8 = Dispensa

# Um perfil por ramo. O radar avisa quando o objeto da licitação casa com
# algum `termos` e não casa com nenhum `excluir`.
[[perfil]]
nome = "impressos"
termos = ["impressão", "gráfica", "folder", "cartilha"]
excluir = ["impressora", "toner", "cartucho"]

[[perfil]]
nome = "papel"
termos = ["papel sulfite", "papel offset"]
"""
