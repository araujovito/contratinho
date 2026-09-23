"""Dados oficiais do edital: datas de proposta, valor estimado e anexos.

O índice de busca do portal (`portal.py`) é bom para descobrir editais, mas
carrega vigência do contrato no lugar das datas de proposta e devolve o valor
vazio na prática. As duas informações que o usuário precisa para decidir — até
quando dá para agir e quanto vale — só existem na rota de item da API do PNCP,
junto com a lista de arquivos do edital.

Este módulo roda dentro do clique do usuário, então faz **uma** tentativa com
timeout curto. O PNCP responde 502/503 com frequência; quando isso acontece, a
página continua mostrando o que já tinha e o link para o portal. Esperar seis
retentativas com o usuário olhando para a tela seria pior do que não enriquecer.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from curl_cffi import requests
from curl_cffi.requests.errors import RequestsError

API = "https://pncp.gov.br/api/pncp/v1"
TIMEOUT = 8

# numeroControlePNCP: "29138377000193-1-000001/2026"
_ID = re.compile(r"^(?P<cnpj>\d{14})-\d+-(?P<sequencial>\d+)/(?P<ano>\d{4})$")


class DadosIndisponiveis(RuntimeError):
    """O PNCP não respondeu ou devolveu algo que não dá para aproveitar."""


def partes_do_id(pncp_id: str) -> tuple[str, int, int]:
    """Quebra o identificador PNCP em CNPJ, ano e sequencial."""
    casamento = _ID.match((pncp_id or "").strip())
    if not casamento:
        raise DadosIndisponiveis(f"identificador PNCP fora do formato esperado: {pncp_id!r}")
    return (
        casamento["cnpj"],
        int(casamento["ano"]),
        int(casamento["sequencial"]),
    )


def _data(valor: Any) -> date | None:
    if not valor or not isinstance(valor, str):
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _numero(valor: Any) -> float | None:
    if valor is None or isinstance(valor, bool):
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _get(client: Any, caminho: str) -> Any:
    try:
        resposta = client.get(f"{API}{caminho}", timeout=TIMEOUT)
    except RequestsError as erro:
        raise DadosIndisponiveis(f"PNCP não respondeu: {erro}") from erro
    codigo = getattr(resposta, "status_code", 0)
    if codigo == 404:
        raise DadosIndisponiveis("edital não encontrado na API do PNCP")
    if codigo != 200:
        raise DadosIndisponiveis(f"PNCP devolveu HTTP {codigo}")
    try:
        return resposta.json()
    except ValueError as erro:
        raise DadosIndisponiveis("PNCP devolveu conteúdo que não é JSON") from erro


def buscar_detalhe(client: Any, cnpj: str, ano: int, sequencial: int) -> dict[str, Any]:
    """Datas de proposta e valor estimado, direto da rota de item.

    Aqui estão `dataAberturaProposta` e `dataEncerramentoProposta`, que são as
    datas que importam para decidir — e não a vigência do contrato.
    """
    bruto = _get(client, f"/orgaos/{cnpj}/compras/{ano}/{sequencial}")
    if not isinstance(bruto, dict):
        raise DadosIndisponiveis("resposta de item em formato inesperado")
    return {
        "abertura": _data(bruto.get("dataAberturaProposta")),
        "encerramento": _data(bruto.get("dataEncerramentoProposta")),
        "publicacao": _data(bruto.get("dataPublicacaoPncp")),
        "valor": _numero(bruto.get("valorTotalEstimado")),
        "modalidade": bruto.get("modalidadeNome") or "",
    }


def _arquivo(bruto: dict[str, Any]) -> dict[str, str] | None:
    """Normaliza um item da lista de arquivos.

    A rota devolve `url` (download direto) e `uri` (endereço do recurso na API);
    aceitamos as duas porque o portal já trocou entre elas.
    """
    endereco = bruto.get("url") or bruto.get("uri") or ""
    if not endereco:
        return None
    titulo = bruto.get("titulo") or bruto.get("nomeArquivo") or "Documento do edital"
    return {
        "titulo": str(titulo).strip(),
        "tipo": str(bruto.get("tipoDocumentoNome") or "").strip(),
        "url": str(endereco).strip(),
    }


def buscar_arquivos(client: Any, cnpj: str, ano: int, sequencial: int) -> list[dict[str, str]]:
    """Lista os documentos publicados do edital, com endereço de download."""
    bruto = _get(client, f"/orgaos/{cnpj}/compras/{ano}/{sequencial}/arquivos")
    if not isinstance(bruto, list):
        raise DadosIndisponiveis("resposta de arquivos em formato inesperado")
    arquivos = [_arquivo(item) for item in bruto if isinstance(item, dict)]
    ativos = [arquivo for arquivo in arquivos if arquivo]
    return ativos


def consultar(pncp_id: str, *, client: Any | None = None) -> dict[str, Any]:
    """Detalhe + arquivos de um edital. Levanta `DadosIndisponiveis` se falhar.

    Os arquivos são opcionais: edital sem anexo publicado é comum e não pode
    invalidar as datas, que são a parte mais importante.
    """
    cnpj, ano, sequencial = partes_do_id(pncp_id)
    proprio = client is None
    client = client or requests.Session(impersonate="chrome")
    try:
        dados = buscar_detalhe(client, cnpj, ano, sequencial)
        try:
            dados["arquivos"] = buscar_arquivos(client, cnpj, ano, sequencial)
        except DadosIndisponiveis:
            dados["arquivos"] = []
        return dados
    finally:
        if proprio and hasattr(client, "close"):
            client.close()


def enriquecer(opportunity, *, client: Any | None = None) -> bool:
    """Completa uma oportunidade com os dados oficiais. Devolve se algo mudou.

    Nunca levanta exceção: é chamada durante uma requisição web, e o PNCP fora
    do ar não pode derrubar a página. Grava `enrichment_checked_at` mesmo no
    fracasso, para que um PNCP instável não vire uma tentativa por clique.
    """
    from django.utils import timezone

    campos = ["enrichment_checked_at"]
    opportunity.enrichment_checked_at = timezone.now()
    mudou = False
    try:
        dados = consultar(opportunity.pncp_id, client=client)
    except DadosIndisponiveis:
        opportunity.save(update_fields=campos)
        return False

    for atributo, chave in (
        ("proposal_opening_date", "abertura"),
        ("deadline", "encerramento"),
        ("publication_date", "publicacao"),
    ):
        valor = dados.get(chave)
        if valor and getattr(opportunity, atributo) != valor:
            setattr(opportunity, atributo, valor)
            campos.append(atributo)
            mudou = True

    if dados.get("valor") is not None and opportunity.value is None:
        opportunity.value = dados["valor"]
        campos.append("value")
        mudou = True

    arquivos = dados.get("arquivos") or []
    if arquivos != opportunity.documents:
        opportunity.documents = arquivos
        campos.append("documents")
        mudou = True

    opportunity.enriched_at = timezone.now()
    campos.append("enriched_at")
    opportunity.save(update_fields=campos)
    return mudou


def precisa_enriquecer(opportunity, *, horas: int = 6) -> bool:
    """Enriquece no primeiro clique e revisita de tempos em tempos.

    O intervalo existe porque prazo e anexos mudam: órgão republica edital,
    prorroga data, adiciona errata. Reconsultar a cada clique seria abuso da
    API; nunca reconsultar mostraria prazo vencido como se valesse.
    """
    from datetime import timedelta

    from django.utils import timezone

    if opportunity.enrichment_checked_at is None:
        return True
    return opportunity.enrichment_checked_at < timezone.now() - timedelta(hours=horas)
