# fixtures

`contratacoes_proposta.json` é uma resposta de `GET /contratacoes/proposta`
(API de Consulta do PNCP, v1).

> **Pendente:** este arquivo foi montado a partir do contrato documentado do
> `RecuperarCompraPublicacaoDTO` — o PNCP respondeu 504 em todas as tentativas
> de gravação. Regravar com uma resposta real antes de marcar a v0.1.0:
>
> ```
> curl "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta?dataFinal=20260101&codigoModalidadeContratacao=6&pagina=1&tamanhoPagina=10" \
>   | python -m json.tool > tests/fixtures/contratacoes_proposta.json
> ```
>
> Os registros foram escolhidos para cobrir os casos que importam: um que casa,
> um que só parece casar (impressora), um fora da UF, um sem valor estimado.
