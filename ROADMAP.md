# Roadmap

A v0.1.0 faz uma coisa: uma varredura, filtrada, sem repetir aviso, no
terminal. O que está aqui embaixo **não** está implementado, e foi deixado de
fora para que a v0.1 pudesse sair.

## Antes de marcar a v0.1.0

- [ ] Regravar `tests/fixtures/contratacoes_proposta.json` com uma resposta
      real de `/contratacoes/proposta` (a API respondeu 504 em todas as
      tentativas durante o desenvolvimento). Ver `tests/fixtures/README.md`.
- [ ] Rodar `radar check` contra o PNCP de verdade e conferir a saída.

## Depois

- **Data de encerramento por edital.** O `RecuperarCompraPublicacaoDTO` traz
  `dataEncerramentoProposta`, mas o modelo do `pypncp` ignora o campo. O certo
  é abrir um PR lá acrescentando-o, em vez de manter um cliente paralelo aqui.
- **Outros canais de notificação.** E-mail e Telegram. `saida.py` já está
  isolado para isso: é acrescentar um módulo, não mexer no resto.
- **Agendador embutido.** Só se ficar claro que cron e Agendador de Tarefas não
  atendem. Hoje atendem.
- **Interface web.** Fora de escopo enquanto for de um usuário só.
- **Histórico de preços.** Casar contratações com os preços homologados para
  estimar a faixa de disputa. É outro produto.
- **Multiusuário.** Idem.
