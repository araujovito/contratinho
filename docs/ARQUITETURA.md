# ADR 001 — Monólito modular Django

Status: aceito para o MVP.

Django oferece autenticação, sessões, CSRF, ORM e migrações integrados. Preservamos a
CLI e as regras puras existentes; a camada web mantém contas e acompanhamento.
HTML renderizado no servidor reduz infraestrutura e funciona sem JavaScript.
PostgreSQL é o banco previsto para produção; SQLite serve ao desenvolvimento local.

Editais são compartilhados. Preferências e acompanhamentos pertencem ao usuário;
toda consulta ou alteração de dados privados deve filtrar pelo usuário autenticado.
Coleta ocorre por comando independente, nunca durante navegação. A ingestão é
idempotente por identificador PNCP. Falhas não devem apagar o último catálogo válido.

Evolução: coletor paginado com checkpoints, retentativas limitadas e histórico de
execuções; fila/outbox para notificações; classificação pré-calculada por mercado.
Adicionar infraestrutura conforme medições. Não há evidência para microserviços agora.

Referências:
- https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- https://www.gov.br/pncp/pt-br/pncp/manuais

A coleta web usa a busca oficial do portal porque a API versionada de consulta não
respondeu durante a validação de 22/09/2026. O adaptador fica isolado em `portal.py`,
aplica retentativas limitadas e só publica depois de concluir a rede. A rota de busca
não possui contrato público versionado, portanto deve ser monitorada. Fixtures de
testes são sintéticas; não afirmar cobertura completa nem frescor sem evidência.
