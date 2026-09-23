"""Enriquecimento opcional das oportunidades em linguagem simples."""

from __future__ import annotations

import hashlib
import os

from openai import OpenAI
from pydantic import BaseModel, Field

from .models import Opportunity


class OpportunitySummary(BaseModel):
    summary: str = Field(description="Uma frase direta explicando o que o órgão quer contratar.")
    key_points: list[str] = Field(description="Até cinco informações práticas presentes na fonte.")
    cautions: list[str] = Field(description="Até três pontos que o fornecedor precisa conferir.")


SYSTEM_PROMPT = """Você ajuda pequenos fornecedores brasileiros a entender compras públicas.
Reescreva somente o que estiver na fonte, em português simples e respeitoso. Não invente valores,
documentos, prazos ou exigências. Se uma informação não estiver disponível, não a inclua.
O resumo deve começar pelo produto ou serviço procurado, sem linguagem jurídica desnecessária.
Use no máximo cinco pontos principais e três alertas. Não diga que analisou o edital completo."""


def source_hash(item: Opportunity) -> str:
    source = "\n".join(
        [
            item.title,
            item.agency,
            item.uf,
            str(item.value or ""),
            str(item.publication_date or ""),
            str(item.proposal_opening_date or ""),
            str(item.deadline or ""),
        ]
    )
    return hashlib.sha256(source.encode()).hexdigest()


def summarize(item: Opportunity, *, client: OpenAI | None = None) -> OpportunitySummary:
    client = client or OpenAI()
    model = os.getenv("RADAR_AI_MODEL", "gpt-4o-mini")
    response = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Objeto publicado: {item.title}\n"
                    f"Órgão: {item.agency}\nUF: {item.uf or 'não informada'}\n"
                    f"Valor: {item.value or 'não informado'}\n"
                    f"Publicação: {item.publication_date or 'não informada'}\n"
                    f"Abertura: {item.proposal_opening_date or 'não informada'}\n"
                    f"Encerramento: {item.deadline or 'não informado'}"
                ),
            },
        ],
        text_format=OpportunitySummary,
    )
    if response.output_parsed is None:
        raise RuntimeError("A IA não retornou um resumo estruturado.")
    return response.output_parsed
