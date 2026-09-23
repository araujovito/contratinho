# Aplicação web — desenvolvimento

Requer Python 3.12 ou 3.13. Na raiz do repositório:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,web]"
export CONTRATINHO_DEBUG=1
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Abra http://127.0.0.1:8000, crie uma conta com nome de usuário e senha,
escolha mercado e estado. As migrações criam cinco mercados iniciais.
O banco começa sem editais; nenhuma oportunidade fictícia é apresentada como real.

O painel próprio de gestão em http://127.0.0.1:8000/admin/ entra automaticamente
quando `CONTRATINHO_DEBUG=1` e o acesso vem da própria máquina. Ele reúne uma visão
geral, mercados, oportunidades e usuários em um menu curto. Termos são editados
em texto separado por vírgulas e mercados de uma oportunidade usam caixas de
seleção simples. O usuário técnico `admin-local` não possui senha utilizável.
Fora desse modo, a área exige uma conta administrativa autenticada normalmente.
O atalho também é recusado quando a requisição chega com cabeçalho de proxy
(`X-Forwarded-For` e equivalentes): atrás de um nginx no mesmo host, `REMOTE_ADDR`
é `127.0.0.1` para todo visitante, e sozinho ele deixaria de provar acesso local.

## Coleta compartilhada

Em outro terminal com o mesmo ambiente:

```bash
python manage.py sync_pncp
```

A coleta consulta a busca pública usada pelo portal, limitada a editais que estão
recebendo propostas no RJ e aos termos cadastrados nos mercados. Ela baixa tudo
antes de iniciar a transação e atualiza por identificador PNCP. Classifica o
catálogo para todos os mercados. Rodadas
repetidas preservam os acompanhamentos. Não agenda tarefas automaticamente.
Execute apenas um coletor por vez nesta versão; a coleta ainda carrega o lote
em memória e não é adequada a um catálogo nacional de grande volume.

Publicação, início e encerramento vêm do índice de busca. Cada oportunidade recebe
um link canônico para a página pública do edital no PNCP. Editais antigos podem
continuar no catálogo; a última consulta é exibida. A reconciliação de cancelamentos
e encerramentos ainda é requisito para o piloto. Os resultados não têm filtro por
esfera administrativa; UF não significa governo estadual.

### Diagnóstico de conectividade em 22/09/2026

DNS, TLS e a página inicial do PNCP responderam normalmente. As rotas versionadas
de consulta, detalhe e Swagger aceitaram a conexão, mas não enviaram resposta em
15 a 30 segundos. O cliente anterior também fazia três tentativas de 30 segundos e
buscava todas as páginas, o que transformava a falha em uma espera longa.

A rota oficial usada pelo próprio portal (`/api/search/`) respondeu com dados reais,
mas o balanceador encerrou conexões de clientes Python HTTP genéricos. O coletor
agora usa a mesma negociação TLS de um navegador e retentativas limitadas. Na
validação local, processou 542 editais em aproximadamente 15 segundos; os 542 tinham
datas e URL oficial, e três URLs amostradas responderam HTTP 200. A integração
anterior permanece disponível para diagnóstico com
`python manage.py sync_pncp --fonte consulta --dias 30`.

A busca do portal não possui contrato público versionado. Mudanças no portal podem
exigir ajuste no adaptador; falhas preservam o catálogo anterior. Testes automatizados
usam respostas sintéticas e nunca acessam a rede.

## Dados oficiais e anexos, no clique

O índice de busca resolve a descoberta, mas não a decisão: ele entrega
`data_inicio_vigencia` e `data_fim_vigencia`, que são a vigência do contrato, e
`valor_global` vazio em todos os 539 editais coletados na validação de
23/09/2026. Um cartão dizia "prazo para agir 05/02/2027" para um edital
publicado em 2025.

As datas de proposta e o valor estimado existem na rota de item
(`/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}`), e os documentos em
`/arquivos`. Como são uma consulta por edital, elas acontecem no primeiro
clique do detalhe — o momento em que o usuário decide e a consulta se paga —
e não durante a coleta.

`contratinho/web/documentos.py` faz **uma** tentativa, com timeout de oito
segundos e sem retentativa: a chamada roda dentro da requisição web. Quando
falha, a página mantém o que já tinha, marca a data como não confirmada e
oferece o link do portal. `enrichment_checked_at` é gravado mesmo no fracasso,
então um PNCP instável não vira uma consulta por clique; `precisa_enriquecer`
reconsulta depois de seis horas, porque prazo prorrogado e errata precisam
aparecer.

> **Não verificado contra a API real.** As rotas `/api/pncp/v1/` responderam
> 502 e 503 durante toda a implementação, e o próprio `/api/search/` passou a
> responder 503 depois da coleta. O mapeamento de campos
> (`dataAberturaProposta`, `dataEncerramentoProposta`, `valorTotalEstimado`,
> e `url`/`uri` nos arquivos) segue o contrato documentado do PNCP, mas ainda
> não foi confirmado contra uma resposta de verdade. Os testes usam respostas
> sintéticas. O caminho de falha, esse sim, foi verificado na tela.

## Aviso por e-mail

O problema que abriu o projeto foi "quem esquece de olhar, perde o prazo". Um
site não resolve isso — exige lembrar de entrar. O comando abaixo é o que fecha
a promessa, e foi feito para o cron:

```bash
python manage.py send_alerts --seco    # mostra o que sairia, sem enviar
python manage.py send_alerts
```

Sem `CONTRATINHO_SMTP_HOST`, o Django imprime a mensagem no terminal: dá para ler o
alerta inteiro sem configurar nada. Para enviar de verdade:

- `CONTRATINHO_SMTP_HOST`, `CONTRATINHO_SMTP_PORT` (padrão 587), `CONTRATINHO_SMTP_USER`,
  `CONTRATINHO_SMTP_PASSWORD`, `CONTRATINHO_SMTP_TLS` (padrão ligado).
- `CONTRATINHO_FROM_EMAIL`: remetente.
- `CONTRATINHO_SITE_URL`: endereço público, porque o e-mail é lido fora do navegador
  e link relativo não serve.

Cada pessoa recebe no máximo oito oportunidades por mensagem; o resto fica no
site e o e-mail diz quantas são. Edital com prazo vencido nunca entra. O envio
é registrado em `Alert` só **depois** de o SMTP aceitar, então falha devolve o
edital para a próxima rodada: repetir incomoda, perder prazo custa dinheiro.
Uma rodada não para por causa de um envio que falhou.

No cron, junto da coleta:

```cron
0 7 * * 1-5  cd /caminho && python manage.py sync_pncp && python manage.py send_alerts
```

## Explicações em linguagem simples

O texto oficial permanece intacto. A interface remove apenas prefixos de origem e
melhora a capitalização para leitura. Opcionalmente, um processo separado pode gerar
uma explicação curta, pontos principais e alertas em campos próprios:

```bash
export OPENAI_API_KEY="..."
export CONTRATINHO_AI_MODEL="gpt-4o-mini"  # opcional
python manage.py summarize_opportunities --limit 20
```

O comando ignora oportunidades cuja fonte não mudou; `--force` refaz a análise.
Ele usa saída estruturada, não roda durante uma requisição web e nunca substitui o
objeto publicado. A tela identifica o conteúdo automático, permite abrir o objeto
original e mantém o link para o edital completo no PNCP. A versão atual resume os
metadados coletados; download e análise dos anexos completos é a próxima etapa e
depende de uma rota de documentos estável no PNCP.

## Verificação

```bash
CONTRATINHO_DEBUG=1 pytest -q
ruff check .
ruff format --check .
CONTRATINHO_DEBUG=1 python manage.py check
CONTRATINHO_DEBUG=1 python manage.py makemigrations --check --dry-run
```

## Configuração e próximos requisitos de operação

- `CONTRATINHO_DEBUG=1`: exclusivamente local; padrão é desativado.
- `CONTRATINHO_SECRET_KEY`: segredo obrigatório fora do desenvolvimento, nunca versionar.
- `CONTRATINHO_ALLOWED_HOSTS`: hosts permitidos separados por vírgula.
- `DATABASE_URL`: conexão PostgreSQL; sem ela, usa SQLite local.

Produção usa cookies seguros, redirecionamento HTTPS e HSTS. Configurar TLS,
servidor WSGI e entrega de estáticos (`collectstatic`) antes de publicar; não usar
`runserver`. A configuração de proxy deve ser específica da infraestrutura.

A base inclui autenticação Django, hash de senha, validação de senha, CSRF,
escape de HTML, migrações, paginação e testes de isolamento. Isso não substitui
uma revisão de segurança. Antes de abrir cadastro público faltam recuperação e
verificação de e-mail, limitação de tentativas, exclusão de conta, política de
privacidade, backups com restauração testada, monitoramento, validação real do
PNCP e testes com PostgreSQL. Alertas por e-mail ainda não são enviados.
