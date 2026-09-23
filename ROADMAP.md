# Roadmap do produto

Atualizado em 23/09/2026. O que está marcado foi feito **e verificado**; o que
foi escrito mas não confirmado contra o mundo real aparece como pendente, com o
motivo.

## Feito

1. [x] Público, proposta, MVP e métricas em `docs/PRODUTO.md`.
2. [x] Arquitetura modular e fronteiras em `docs/ARQUITETURA.md`.
3. [x] Núcleo puro: leitura de regras e casamento de termos sem rede nem banco.
4. [x] CLI `init`/`check` com estado em SQLite, sem repetir aviso.
5. [x] Conta, sessão e configuração guiada de mercado.
6. [x] Catálogo paginado com fonte, atualização e cartões de decisão.
7. [x] Acompanhamento privado com etapas.
8. [x] Coleta compartilhada pela busca do portal, idempotente por identificador.
9. [x] Isolamento entre contas, autenticação e ingestão testados.
10. [x] Plural do português no casamento (`serviços gráficos`, `materiais`).
11. [x] Exclusões dos mercados, extraídas de falso positivo real.
12. [x] Admin sem senha recusado atrás de proxy.
13. [x] **Aviso por e-mail** — o canal que fecha a promessa original.
14. [x] Selo de prazo encerrado nas telas.
15. [x] Mapa competitivo com preços em `docs/CONCORRENTES.md`.
16. [x] Contrato de produto e de dados em `docs/CONTRATO.md`.

## Antes de qualquer coisa nova

17. [ ] **Confirmar o mapeamento da rota de item do PNCP contra resposta real.**
        Datas de proposta, valor estimado e anexos foram implementados e
        testados só com respostas sintéticas — a rota respondeu 502/503 o dia
        inteiro. Enquanto isso não for feito, o prazo exibido pode ser a
        vigência do contrato e o valor segue ausente. Destrava os itens 19 e 20.
18. [ ] **Regravar a fixture da CLI** com resposta real de
        `/contratacoes/proposta`. Ver `tests/fixtures/README.md`.
19. [ ] **Recortar o teto em R$ 80 mil**, a faixa exclusiva ME/EPP, no lugar dos
        R$ 250 mil. Depende do item 17: sem valor, não há o que filtrar.
20. [ ] **Marcar no cartão quando o edital é exclusivo ME/EPP.** É o dado que
        mais muda a decisão de quem está começando, e nenhum concorrente
        destaca.

## Piloto

21. [ ] Reconciliar cancelamento e revogação — hoje só o prazo vencido é
        detectado, pela data.
22. [ ] Recuperação e verificação de e-mail, limite de tentativas, exclusão de
        conta, política de privacidade.
23. [ ] Backup com restauração testada, monitoramento e teste com PostgreSQL.
24. [ ] Coleta com checkpoint e retomada: hoje carrega o lote em memória e roda
        um coletor por vez.
25. [ ] Limpeza do catálogo antigo, preservando o que alguém acompanha.
26. [ ] Deploy: TLS, servidor WSGI, `collectstatic`.

## Validação, que é o buraco maior

27. [ ] **Conversar com fornecedores do RJ.** Nada aqui foi visto por quem vende
        para o governo. O `PRODUTO.md` marca as métricas como pendentes e não há
        validação comercial. Uma conversa de trinta minutos provavelmente
        reordena metade desta lista.
28. [ ] Definir metas numéricas de ativação e retorno, depois das entrevistas.

## Depois, e só depois

29. [ ] WhatsApp como canal — é o padrão do segmento, e tem custo e burocracia
        de API que só se justificam com usuário validado.
30. [ ] Análise dos anexos do edital para extrair exigências, com citação da
        página de origem.
31. [ ] Histórico e preços de referência.
32. [ ] Publicar no PyPI e marcar a v0.1.0 — hoje o README não manda instalar
        por lá, porque não existe lá.
33. [ ] Cobrança. O piso do mercado é R$ 44,90/mês; ver `docs/CONCORRENTES.md`.

## Fora de escopo por enquanto

Envio automático de propostas, recomendação jurídica, decisão automática de
habilitação, robô de lances, marketplace, multiusuário por empresa e
microserviços.
