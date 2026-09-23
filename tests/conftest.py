from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def pagina_proposta() -> dict:
    """Resposta real de /contratacoes/proposta, gravada da API."""
    return json.loads((FIXTURES / "contratacoes_proposta.json").read_text(encoding="utf-8"))
