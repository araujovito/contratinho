"""Casamento de perfis contra licitações.

Módulo puro: entra `Licitacao` + `Config`, sai `Achado`. Sem rede, sem banco,
sem I/O — a suíte de testes exercita a regra de negócio direto, sem mock.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from functools import lru_cache

from radar_pncp.config import Config, Perfil


@dataclass(frozen=True, slots=True)
class Licitacao:
    """O que o radar precisa saber de uma contratação, independente da fonte.

    Existe para que `filtro` não importe pypncp: a conversão fica em `fonte`.
    """

    id: str
    objeto: str
    orgao: str
    uf: str | None
    modalidade: str
    modalidade_id: int | None
    valor: float | None
    encerramento: date | None
    publicacao: date | None
    complemento: str = ""
    url: str | None = None
    abertura: date | None = None

    @property
    def texto(self) -> str:
        return f"{self.objeto} {self.complemento}".strip()


@dataclass(frozen=True, slots=True)
class Achado:
    """Uma licitação que casou com um perfil, e por qual termo."""

    licitacao: Licitacao
    perfil: str
    termos: tuple[str, ...]


def normalizar(texto: str) -> str:
    """Caixa baixa, sem acento, espaços colapsados.

    'Aquisição de  PAPEL Sulfite' -> 'aquisicao de papel sulfite'
    """
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


# Plural em português, sobre texto já sem acento. Cada entrada é
# (final do plural, final do singular): 'materiais' -> 'material',
# 'licitacoes' -> 'licitacao', 'homens' -> 'homem'.
_PLURAIS = (
    ("oes", "ao"),
    ("aes", "ao"),
    ("aos", "ao"),
    ("eis", "el"),
    ("ais", "al"),
    ("ois", "ol"),
    ("uis", "ul"),
    ("is", "il"),
    ("ns", "m"),
    ("res", "r"),
    ("zes", "z"),
    ("ses", "s"),
    ("s", ""),
)

# Palavra curta é preposição ou artigo ('de', 'da', 'em'): não se pluraliza.
_MINIMO_PARA_PLURAL = 3


def _singular(palavra: str) -> str:
    """Reduz uma palavra ao singular provável, sem dicionário.

    Heurística, não morfologia: erra em casos como 'lapis', que já é singular.
    O erro é barato — o padrão gerado aceita as duas formas de qualquer jeito.
    """
    if len(palavra) < _MINIMO_PARA_PLURAL:
        return palavra
    for plural, singular in _PLURAIS:
        if palavra.endswith(plural) and len(palavra) - len(plural) + len(singular) >= 2:
            return palavra[: -len(plural)] + singular
    return palavra


def _formas(palavra: str) -> str:
    """Fragmento de regex que casa a palavra no singular e no plural.

    'material' -> 'materia(?:l|is)'   'licitacao' -> 'licitac(?:ao|oes|aos|aes)'
    """
    if len(palavra) < _MINIMO_PARA_PLURAL:
        return re.escape(palavra)
    raiz = _singular(palavra)
    if raiz.endswith("ao"):
        return re.escape(raiz[:-2]) + r"(?:ao|oes|aos|aes)"
    if raiz.endswith(("al", "el", "ol", "ul", "il")):
        return re.escape(raiz[:-1]) + r"(?:l|is)"
    if raiz.endswith("m"):
        return re.escape(raiz[:-1]) + r"(?:m|ns)"
    if raiz.endswith(("r", "z", "s")):
        # 'es' é a forma do português ('lugar' -> 'lugares'); 's' cobre o
        # estrangeirismo que o edital usa assim mesmo ('toner' -> 'toners').
        return re.escape(raiz) + r"(?:es|s)?"
    return re.escape(raiz) + r"s?"


@lru_cache(maxsize=2048)
def _padrao(termo: str) -> re.Pattern[str]:
    """Regex de um termo: palavra inteira, plural tolerado, espaço flexível.

    Palavra inteira evita que 'impressão' case com 'impressora' — a razão de
    `excluir` existir seria metade perdida se a busca fosse substring solta.

    O plural vale para **cada** palavra, não só a última: em edital, 'serviços
    gráficos' e 'materiais de limpeza' são a forma comum de escrever, e um
    termo cadastrado no singular precisa achar as duas.
    """
    palavras = [_formas(p) for p in normalizar(termo).split()]
    if not palavras:
        return re.compile(r"(?!)")  # termo vazio nunca casa
    return re.compile(rf"\b{r'[\s\-/]+'.join(palavras)}\b")


def casa(texto: str, termo: str) -> bool:
    return bool(_padrao(termo).search(normalizar(texto)))


def termos_encontrados(texto: str, termos: list[str]) -> tuple[str, ...]:
    normalizado = normalizar(texto)
    return tuple(t for t in termos if _padrao(t).search(normalizado))


def aplicar_perfil(licitacao: Licitacao, perfil: Perfil) -> Achado | None:
    """Casa se bater algum `termos` e nenhum `excluir`."""
    texto = licitacao.texto
    if any(casa(texto, excluido) for excluido in perfil.excluir):
        return None
    encontrados = termos_encontrados(texto, perfil.termos)
    if not encontrados:
        return None
    return Achado(licitacao=licitacao, perfil=perfil.nome, termos=encontrados)


def passa_filtros_globais(licitacao: Licitacao, config: Config) -> bool:
    """UF, faixa de valor e modalidade — a seção [radar]."""
    radar = config.radar
    if radar.uf and (licitacao.uf or "").upper() not in radar.uf:
        return False
    if radar.modalidades and licitacao.modalidade_id not in radar.modalidades:
        return False
    valor = licitacao.valor
    if radar.valor_minimo is not None and (valor is None or valor < radar.valor_minimo):
        return False
    if radar.valor_maximo is not None and valor is not None and valor > radar.valor_maximo:
        return False
    return True


def filtrar(licitacoes: list[Licitacao], config: Config) -> list[Achado]:
    """Aplica [radar] e depois os perfis, na ordem em que foram declarados.

    Uma licitação rende no máximo um achado: vale o primeiro perfil que casar,
    para não avisar duas vezes do mesmo edital.
    """
    achados: list[Achado] = []
    for licitacao in licitacoes:
        if not passa_filtros_globais(licitacao, config):
            continue
        for perfil in config.perfil:
            achado = aplicar_perfil(licitacao, perfil)
            if achado is not None:
                achados.append(achado)
                break
    return achados
