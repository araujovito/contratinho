# radar-pncp

Avisa quando aparece licitação do seu ramo no PNCP, dentro do prazo de proposta.

Quem vende para o governo hoje abre o portal do PNCP todo dia e procura na mão.
Quem esquece de olhar, perde o prazo. O radar faz essa varredura uma vez por
execução, filtra pelo que você definiu num arquivo de regras, e imprime **só o
que é novo** — o que já foi avisado não volta.

O `radar init` já sai com um escopo estreito: **contratos de até R$ 250 mil no
Rio de Janeiro**. É um recorte de partida, não um limite do programa — ampliar
é editar duas linhas do `radar.toml`. Começar largo é receber cem avisos no
primeiro dia e parar de ler todos eles.

## Em três comandos

```bash
pip install radar-pncp     # requer Python 3.12+
radar init          # cria radar.toml com um exemplo comentado
radar check         # consulta o PNCP e imprime as licitações novas
```

Saída:

```
  3 licitação(ões) nova(s) — propostas abertas nos próximos 30 dias
┏━━━━━━━━━━━┳━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Perfil    ┃ UF ┃ Objeto                                       ┃        Valor ┃
┡━━━━━━━━━━━╇━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ impressos │ RJ │ Contratação de empresa especializada em      │ R$ 184.500,00│
│           │    │ serviços gráficos para impressão de carti…   │              │
│           │    │ MUNICIPIO DO RIO DE JANEIRO · Pregão         │              │
│           │    │ termos: impressão, cartilha                  │              │
│           │    │ https://pncp.gov.br/app/editais/…            │              │
└───────────┴────┴──────────────────────────────────────────────┴──────────────┘
```

Rodar de novo no mesmo dia não repete nada. É isso que torna o comando
agendável: coloque no cron e só receba e-mail do cron quando houver saída.

```cron
0 8 * * 1-5  cd /home/voce/radar && radar check
```

## As regras

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

[[perfil]]
nome = "papel"
termos = ["papel sulfite", "papel offset"]
```

- `termos` e `excluir` casam **palavra inteira**, sem acento e sem ligar para
  caixa, com plural tolerado: `gráfica` acha `GRÁFICAS`, mas `impressão` não
  acha `impressora`.
- Uma licitação rende no máximo um aviso: vale o primeiro perfil que casar.
- Sem `[radar]`, nada é filtrado por UF, valor ou modalidade.
- `valor_maximo` não descarta edital **sem** valor estimado — o PNCP deixa o
  campo vazio com frequência, e sumir com esses seria esconder licitação que
  provavelmente cabe no teto. Se incomodar, use `valor_minimo` junto.
- `uf` e a faixa de valor são aplicados aqui, depois do download: a API de
  consulta só aceita filtro por modalidade. Estreitar o escopo deixa a lista
  legível, não deixa a consulta mais leve.

## Opções do `check`

| Opção | O que faz |
|---|---|
| `--dias N` | janela de encerramento das propostas (padrão: 30) |
| `--seco` | imprime sem marcar como avisado |
| `--tudo` | mostra também o que já foi avisado, sem tocar no estado |
| `--config` / `--db` | caminhos do arquivo de regras e do banco |

`--seco` e `--tudo` servem para calibrar os perfis: ajuste `termos` e `excluir`
até a lista parecer útil, e só então deixe o radar gravar o estado.

## Decisões

**Por que `pypncp` em vez de um cliente próprio.** A biblioteca existe, é
tipada, async, testada e já resolve a paginação da API de consulta. Reescrever
seria trabalho sem ganho — e o que o projeto tem de próprio (as regras) ficaria
sob o ruído de um cliente HTTP escrito à toa.

**Por que SQLite e não um JSON.** O estado é consultado por id a cada rodada e
escrito em processo que pode morrer no meio (é um job de cron). JSON reescrito
inteiro corrompe em interrupção; SQLite dá índice e transação de graça, sem
dependência nova.

**Por que CLI e não serviço web.** O usuário-alvo já tem cron ou Agendador de
Tarefas. Um servidor seria infraestrutura para manter sem nada em troca: não há
multiusuário, não há sessão, não há nada para servir entre uma execução e outra.

**Por que `excluir` existe.** Buscar "impressão" no PNCP traz sobretudo compra
de impressora e toner. Sem lista de exclusão a ferramenta devolve ruído, o
usuário para de ler os avisos, e o radar vira enfeite. É o campo que separa
ferramenta de brinquedo.

**Por que `filtro.py` e `config.py` não conhecem rede nem banco.** São funções
puras sobre dados; a suíte exercita a regra de negócio direto, sem mock. A
tradução do DTO do PNCP para o modelo interno fica em `fonte.py`, que é o único
lugar que precisa mudar se a API mudar.

**Por que a marcação no banco vem depois de imprimir.** Se o processo morrer
entre uma coisa e outra, o aviso se repete na próxima rodada. Repetir incomoda;
perder o prazo custa dinheiro.

## Desenvolvimento

```bash
pip install -e ".[dev]"
pytest          # não toca a rede: as respostas do PNCP vêm de tests/fixtures/
ruff check .
```

## Limitações conhecidas na v0.1

- O DTO do `pypncp` não expõe `dataEncerramentoProposta`, então o radar não
  mostra a data-limite de cada edital. O prazo fica garantido pela janela da
  consulta (`--dias`): tudo que aparece encerra dentro dela.
- A API de consulta do PNCP responde 504 com alguma frequência. O `check` sai
  com código 2 e uma mensagem; num cron, basta tentar de novo mais tarde.

O que ficou de fora de propósito está no [ROADMAP](ROADMAP.md).

## Licença

MIT.
