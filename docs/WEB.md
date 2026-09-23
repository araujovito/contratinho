# Aplicação web — desenvolvimento

Requer Python 3.12 ou 3.13. Na raiz do repositório:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,web]"
export RADAR_DEBUG=1
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Abra http://127.0.0.1:8000, crie uma conta com nome de usuário e senha,
escolha mercado e estado. As migrações criam cinco mercados iniciais.
O banco começa sem editais; nenhuma oportunidade fictícia é apresentada como real.

O painel próprio de gestão em http://127.0.0.1:8000/admin/ entra automaticamente
quando `RADAR_DEBUG=1` e o acesso vem da própria máquina. Ele reúne uma visão
geral, mercados, oportunidades e usuários em um menu curto. Termos são editados
em texto separado por vírgulas e mercados de uma oportunidade usam caixas de
seleção simples. O usuário técnico `admin-local` não possui senha utilizável.
Fora desse modo, a área exige uma conta administrativa autenticada normalmente.

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

## Verificação

```bash
RADAR_DEBUG=1 pytest -q
ruff check .
ruff format --check .
RADAR_DEBUG=1 python manage.py check
RADAR_DEBUG=1 python manage.py makemigrations --check --dry-run
```

## Configuração e próximos requisitos de operação

- `RADAR_DEBUG=1`: exclusivamente local; padrão é desativado.
- `RADAR_SECRET_KEY`: segredo obrigatório fora do desenvolvimento, nunca versionar.
- `RADAR_ALLOWED_HOSTS`: hosts permitidos separados por vírgula.
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
