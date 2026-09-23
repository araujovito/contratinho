# Contratinho

Avisa quando o governo publica um contrato pequeno do seu ramo, dentro do prazo
de proposta.

Quem vende para o governo abre o portal do PNCP todo dia e procura na mão. Quem
esquece de olhar, perde o prazo. O Contratinho faz essa varredura, filtra pelo
que você definiu e **avisa só o que é novo** — o que já foi avisado não volta.

O foco é o contrato pequeno: dispensa eletrônica e pregão de baixo valor. Não é
detalhe de escopo, é a tese. Licitação até R$ 80 mil é exclusiva para ME e EPP,
e mais de 70% das dispensas eletrônicas do PNCP em 2026 caem nessa faixa. Todo
concorrente vende "todas as licitações do Brasil" e manda o usuário filtrar;
para quem nunca licitou, isso é o problema, não a solução. O raciocínio inteiro,
com os preços do mercado, está em [docs/CONCORRENTES.md](docs/CONCORRENTES.md).

> **Estado:** em desenvolvimento, sem usuário real ainda. Nada publicado no
> PyPI e nenhuma versão marcada. O que falta para o piloto está no
> [ROADMAP](ROADMAP.md), e o que o produto promete e não promete está em
> [docs/CONTRATO.md](docs/CONTRATO.md).

## Duas interfaces, um núcleo

O casamento de termos e a leitura das regras são **funções puras**, sem rede e
sem banco. Em cima delas existem duas entradas:

| | Para quem | Onde |
|---|---|---|
| **Aplicação web** | o usuário final: conta, mercado, acompanhamento e aviso por e-mail | `contratinho/web/` |
| **CLI** | quem prefere cron e terminal, e o próprio desenvolvimento | `contratinho/cli.py` |

As duas leem o PNCP por caminhos diferentes, por um motivo que vale saber antes
de mexer: ver [Decisões](#decisões).

## Rodar a aplicação web

Requer Python 3.12 ou 3.13.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,web]"
export CONTRATINHO_DEBUG=1
python manage.py migrate
python manage.py sync_pncp          # coleta editais reais do RJ
python manage.py runserver
```

Abra http://127.0.0.1:8000, crie a conta e escolha mercado e estado. Para o
aviso por e-mail (sem SMTP configurado, a mensagem sai no terminal):

```bash
python manage.py send_alerts --seco   # mostra o que sairia
python manage.py send_alerts
```

No cron, que é como isso vive de verdade:

```cron
0 7 * * 1-5  cd /caminho && python manage.py sync_pncp && python manage.py send_alerts
```

Detalhes de configuração, SMTP e painel de gestão: [docs/WEB.md](docs/WEB.md).

## Rodar a CLI

```bash
contratinho init          # cria contratinho.toml comentado
contratinho check         # consulta o PNCP e imprime o que é novo
```

Rodar de novo no mesmo dia não repete nada — é isso que torna o comando
agendável.

### As regras

```toml
[radar]
uf = ["RJ"]
valor_maximo = 250000
# valor_minimo = 10000   # sem mínimo, edital sem valor estimado também aparece
# modalidades = [6, 8]   # 6 = Pregão Eletrônico, 8 = Dispensa

[[perfil]]
nome = "impressos"
termos = ["impressão", "gráfica", "folder", "cartilha"]
excluir = ["impressora", "toner", "cartucho"]
```

- `termos` e `excluir` casam **palavra inteira**, sem acento, sem ligar para
  caixa, e com plural em cada palavra: `serviço gráfico` acha `serviços
  gráficos`, `material de limpeza` acha `materiais de limpeza`, mas `impressão`
  **não** acha `impressora`.
- Uma licitação rende no máximo um aviso: vale o primeiro perfil que casar.
- `valor_maximo` não descarta edital **sem** valor estimado — o PNCP deixa o
  campo vazio com frequência.
- `uf` e faixa de valor são aplicados depois do download: a API só filtra por
  modalidade. Estreitar deixa a lista legível, não a consulta mais leve.

Opções do `check`: `--dias N` (janela), `--seco` (não marca como avisado),
`--tudo` (mostra o que já foi avisado), `--config` e `--db`.

## Decisões

**Por que duas fontes do PNCP.** A CLI usa a API de consulta versionada
(`/api/consulta/v1`, via `pypncp`), que é documentada e estável — mas respondeu
504 durante dias. A web usa a busca do próprio portal (`/api/search/`), que
responde e traz o que precisamos, ao custo de não ter contrato público. É
duplicação consciente: a rota documentada não sustentou o produto sozinha. O
que cada uma entrega, e onde cada uma quebra, está em
[docs/CONTRATO.md](docs/CONTRATO.md).

**Por que SQLite no estado da CLI.** Consulta por id a cada rodada, escrita por
um job de cron que pode morrer no meio. JSON reescrito inteiro corrompe em
interrupção; SQLite dá índice e transação sem dependência nova.

**Por que `excluir` existe.** Buscar "impressão" no PNCP traz sobretudo compra
de impressora e toner. Sem exclusão a ferramenta devolve ruído, o usuário para
de ler os avisos, e vira enfeite. Foi o que aconteceu na primeira tela da web:
uma impressora de cartões entrou em "limpeza" por causa de "rolete de limpeza
contínua".

**Por que o núcleo não conhece rede nem banco.** `filtro.py` e `config.py` são
funções puras sobre dados; a suíte exercita a regra de negócio sem um único
mock. A tradução do PNCP fica isolada, e é o único lugar a mexer se a API mudar.

**Por que a marcação vem depois de avisar.** Se o processo morrer entre imprimir
e gravar, o aviso se repete na próxima rodada. Repetir incomoda; perder o prazo
custa dinheiro.

**Por que o aviso é o produto.** Um site exige que a pessoa lembre de entrar —
que é o problema original. Ver [docs/CONCORRENTES.md](docs/CONCORRENTES.md).

## Desenvolvimento

```bash
pip install -e ".[dev,web]"
CONTRATINHO_DEBUG=1 pytest -q      # 152 testes, nenhum toca a rede
ruff check . && ruff format --check .
CONTRATINHO_DEBUG=1 python manage.py check
```

## Limitações conhecidas

- **Valor estimado ausente na maioria dos editais.** A busca do portal devolve
  o campo vazio; o valor real vem da rota de item, cujo mapeamento ainda não foi
  confirmado contra resposta real.
- **Prazo pode estar errado** até essa confirmação: parte das datas vem da
  vigência do contrato, não do período de propostas.
- **Edital cancelado antes do prazo** continua no catálogo.
- **O PNCP responde 502/503/504 com frequência.** A coleta preserva o catálogo
  anterior e a tela degrada sinalizando.
- **Ninguém que vende para o governo usou isto ainda.** Não há validação.

## Documentação

| Documento | O que tem |
|---|---|
| [docs/CONTRATO.md](docs/CONTRATO.md) | o que prometemos, e o acordo técnico com o PNCP |
| [docs/PRODUTO.md](docs/PRODUTO.md) | público, MVP e métricas |
| [docs/CONCORRENTES.md](docs/CONCORRENTES.md) | mercado, preços e posicionamento |
| [docs/REFERENCIAS_UX.md](docs/REFERENCIAS_UX.md) | direção visual e de linguagem |
| [docs/ARQUITETURA.md](docs/ARQUITETURA.md) | fronteiras dos módulos |
| [docs/WEB.md](docs/WEB.md) | rodar, configurar e operar a web |
| [ROADMAP.md](ROADMAP.md) | o que falta, em ordem |

## Licença

MIT.
