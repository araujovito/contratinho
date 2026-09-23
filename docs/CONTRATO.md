# Contrato

Duas promessas que o Contratinho assume por escrito: a que ele faz a quem usa,
e a que ele depende do PNCP para cumprir. A primeira define o que podemos
afirmar sem mentir. A segunda define o que quebra quando o PNCP muda.

---

# Parte 1 — Contrato com quem usa

## O que o Contratinho promete

1. **Mostrar contratações públicas que combinam com o que você vende**, dentro
   do mercado e do estado que você escolheu.
2. **Avisar por e-mail quando aparecer algo novo**, sem repetir o que já foi
   avisado.
3. **Dizer por que cada oportunidade apareceu** — qual palavra do seu perfil
   casou com o objeto publicado.
4. **Levar você à fonte oficial** em todas as telas, com o identificador PNCP e
   o link do edital.
5. **Dizer quando não sabemos.** Valor não informado aparece como "não
   informado pelo órgão", não como zero nem como campo vazio.

## O que o Contratinho não promete

Isto não é ressalva jurídica de rodapé. É desenho de produto: cada item abaixo
é uma coisa que o sistema **não tem como saber**, e fingir que sabe seria pior
do que calar.

- **Não promete renda nem contrato.** Aparecer na lista não significa que você
  tem chance, que o preço compensa, ou que o órgão vai comprar.
- **Não diz se você está habilitado.** Exigência de documento, certidão,
  atestado de capacidade técnica e regularidade fiscal estão no edital, e só lá.
- **Não substitui a leitura do edital.** O objeto publicado é um resumo; prazo,
  horário, local de entrega e anexos mandam mais do que qualquer tela nossa.
- **Não é consultoria jurídica.** Não interpretamos a lei nem a sua situação.
- **Não garante cobertura completa.** Lemos um portal, o PNCP. Contratação que
  não foi publicada lá, ou publicada com termo que não casa com seu perfil, não
  aparece. Ausência aqui não é prova de ausência no mundo.
- **Não garante que o prazo exibido está certo.** Ver a Parte 2: parte das
  datas vem de um campo que nem sempre é o que parece.
- **Não envia proposta nem participa por você.**

## De onde vem cada informação na tela

| O que você vê | De onde vem | Confiabilidade |
|---|---|---|
| Objeto, órgão, UF, identificador | busca pública do PNCP | alta, é texto publicado |
| "Por que apareceu" | nosso casamento de termos | nossa regra, não do órgão |
| Prazo e início das propostas | rota de item do PNCP, buscada no seu clique | **ver ressalva abaixo** |
| Valor estimado | rota de item do PNCP | frequentemente ausente |
| Anexos para baixar | rota de arquivos do PNCP | o que o órgão publicou |
| Resumo em linguagem simples | modelo de linguagem, quando gerado | **automático, pode errar** |

Todo conteúdo gerado automaticamente é identificado como tal na tela, e o texto
original do órgão fica sempre acessível ao lado. Nunca substituímos o objeto
publicado — acrescentamos leitura, e marcamos que é nossa.

## O que fazemos com seus dados

- **E-mail:** usado para enviar o aviso de oportunidades. Nada além disso.
- **Mercado, estado e editais acompanhados:** ficam na sua conta e não são
  mostrados a outros usuários.
- **Não pedimos CNPJ** para explorar. Você não precisa ter empresa para olhar.

Falta, antes de qualquer cadastro público: recuperação e verificação de e-mail,
exclusão de conta, política de privacidade e backup testado. Está no ROADMAP e
é bloqueio de lançamento, não item desejável.

## Quando o contrato é quebrado

Se o PNCP estiver fora do ar, a tela mostra o que já tínhamos e diz que não
conseguiu confirmar. Preferimos dado velho sinalizado a dado novo inventado.
Nenhuma tela preenche lacuna com estimativa.

---

# Parte 2 — Contrato de dados com o PNCP

Somos um leitor de uma fonte só. Esta parte é o que assumimos sobre ela, e o
que acontece quando a suposição falha.

## As três rotas que usamos

### 1. Busca do portal — `GET www.pncp.gov.br/api/search/`

Descobre editais. É a rota que o próprio site do PNCP consome.

- **Parâmetros:** `q` (termo), `tipos_documento=edital`,
  `status=recebendo_proposta`, `ufs`, `pagina`, `tam_pagina`.
- **Campos que lemos:** `numero_controle_pncp`, `description`/`title`,
  `orgao_nome`, `orgao_cnpj`, `uf`, `ano`, `numero_sequencial`,
  `modalidade_licitacao_id`/`_nome`, `valor_global`, `data_publicacao_pncp`,
  `data_inicio_vigencia`, `data_fim_vigencia`.
- **Estado:** verificada contra respostas reais. 539 editais do RJ processados
  em 43s em 23/09/2026.
- **Não tem contrato público versionado.** É API interna de portal. Pode mudar
  sem aviso.
- **Exige TLS de navegador.** O balanceador encerra conexões de cliente HTTP
  genérico; usamos `curl_cffi` com `impersonate="chrome"`. Não é evasão de
  proteção: é a mesma rota, no mesmo volume, que o navegador faz.

> **Armadilha confirmada:** `data_inicio_vigencia` e `data_fim_vigencia` são a
> **vigência do contrato**, não o período de propostas. Um edital publicado em
> 2025 apareceu com "prazo para agir 05/02/2027". E `valor_global` veio nulo em
> **539 de 539** editais. Por isso a rota 2 existe.

### 2. Item — `GET pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}`

Traz as datas que importam e o valor estimado.

- **Campos que lemos:** `dataAberturaProposta`, `dataEncerramentoProposta`,
  `dataPublicacaoPncp`, `valorTotalEstimado`, `modalidadeNome`.
- **Estado:** ⚠️ **mapeamento não confirmado contra resposta real.** A rota
  respondeu 502/503 durante toda a implementação em 23/09/2026. Os nomes seguem
  o contrato documentado do PNCP; os testes usam respostas sintéticas.
- **Verificar assim, quando o PNCP voltar:** abra qualquer oportunidade e veja
  se o prazo muda e o valor aparece. Se não mudar, o mapeamento em
  `contratinho/web/documentos.py` está errado — é ajuste de uma linha.

### 3. Arquivos — `.../compras/{ano}/{seq}/arquivos`

Lista os documentos para download.

- **Campos que lemos:** `titulo` ou `nomeArquivo`, `tipoDocumentoNome`, e o
  endereço em `url` **ou** `uri` — aceitamos os dois porque o portal já trocou.
- **Estado:** ⚠️ mesma ressalva da rota 2.
- **Anexo é opcional.** Edital sem arquivo publicado é comum e não invalida as
  datas.

## Como cada falha se comporta

| Falha | O que acontece |
|---|---|
| Busca fora do ar | a coleta aborta e **preserva o catálogo anterior** |
| Item/arquivos fora do ar | a página mantém o dado antigo, marca "não confirmada" e oferece o link do PNCP |
| Campo que sumiu do JSON | vira `None`; a tela mostra "não informado" |
| Formato de data inesperado | vira `None`, não levanta exceção |
| Identificador fora do padrão | `DadosIndisponiveis`, sem enriquecimento |

O enriquecimento roda **dentro da requisição web**: uma tentativa, 8 segundos,
sem retentativa. A tentativa é registrada mesmo quando falha, para que um PNCP
instável não vire uma consulta por clique. Reconsulta depois de 6 horas.

## Suposições que, se mudarem, quebram o produto

1. O `numero_controle_pncp` é estável e único — é a chave de "já vi isso".
2. `{cnpj}/{ano}/{sequencial}` continua endereçando o edital nas rotas 2 e 3.
3. `https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}` continua sendo o
   endereço público do edital.
4. `status=recebendo_proposta` continua significando proposta aberta.

## O que não reconciliamos

Edital **cancelado ou revogado antes do prazo** continua no catálogo como se
valesse. Marcamos prazo vencido pela data, mas não sabemos de cancelamento —
isso depende da rota 2, ainda não verificada. É requisito de piloto.

## Testes nunca tocam a rede

Toda a suíte roda com respostas gravadas ou sintéticas. Isso mantém o CI
honesto, e é também o motivo de o mapeamento da rota 2 seguir não confirmado:
teste verde aqui não prova que o PNCP concorda conosco.
