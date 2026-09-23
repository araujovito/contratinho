# Mapa competitivo e norte estratégico

Pesquisa em 23/09/2026, a partir das páginas públicas de preço e produto. Nada
atrás de login foi consultado. Onde o preço não é publicado, está escrito
"sob consulta" — não é estimativa minha.

Este documento complementa `REFERENCIAS_UX.md`, que olhou linguagem e interface.
Aqui o assunto é outro: quem cobra quanto, de quem, e onde sobra espaço.

## O mercado, por preço e por público

| Produto | Preço/mês | Fontes | Canal | Teste |
|---|---|---|---|---|
| Alerta Licitação | R$ 44,90 individual · R$ 54,90 corporativo | 6.441 portais | E-mail, app, WhatsApp (só corporativo) | parcial grátis |
| LicitaCerta | R$ 49 | não publica | **só WhatsApp** | consulta por CNPJ, sem cadastro |
| ContrataX | R$ 59 entrada · R$ 149 com leitura por IA | **só PNCP** | painel, e-mail | não publica |
| VouLicitar | R$ 89 mensal · R$ 59 no anual | não publica | web + app | 3 dias, sem cartão |
| Licita Já | R$ 235 | não publica | e-mail | 14 dias, sem cartão |
| ConLicitação | sob consulta | 6.000+ fontes | boletim por CNAE | 15 dias |
| Effecti | sob consulta | 1.400+ portais | plataforma completa | sob consulta |

Três leituras desse quadro.

**O piso de preço é R$ 44,90.** Não existe espaço para cobrar caro de quem está
começando. Qualquer monetização futura do Radar cabe embaixo de R$ 50 ou é
gratuita — e R$ 50/mês de um público que ainda não ganhou nenhuma licitação é
uma venda difícil, que os concorrentes resolvem prometendo tempo economizado,
não resultado.

**Teste sem cadastro é padrão, não diferencial.** Todo mundo deixa provar antes
de pagar, e a LicitaCerta deixa consultar por CNPJ sem nem criar conta. A
decisão do `PRODUTO.md` de não exigir CNPJ para explorar está certa, mas é
paridade com o mercado, não vantagem.

**Cobertura de fontes é o eixo onde o Radar perde, e é caro disputar.** Effecti
tem 1.400 portais, ConLicitação e Alerta Licitação passam de 6.000. O Radar tem
um: o PNCP. A ContrataX é a prova de que dá para viver disso — também é só PNCP
e transforma isso em argumento de preço baixo. Mas é uma escolha que precisa ser
dita em voz alta, não escondida.

## As duas notícias ruins

### 1. O nicho descrito no PRODUTO.md já está ocupado

O `PRODUTO.md` define o público como "pessoas que desejam começar a fornecer ao
governo", com linguagem cotidiana e decisão guiada. Isso é, quase palavra por
palavra, a LicitaCerta: onboarding por CNPJ em 12 minutos, 3 a 4 alertas por
semana no WhatsApp, resumo feito para decidir em 30 segundos, R$ 49/mês.

E não é só ela. A Effecti — que o `REFERENCIAS_UX.md` classificou como "operação
completa, longe do nosso público" — segmenta os clientes explicitamente por
volume, e o primeiro segmento é **"Iniciantes: menos de 2 licitações por mês"**.
O incumbente não ignora o iniciante; ele já desce até lá.

Isso não mata o projeto. Mas significa que "ser mais simples e mais amigável"
não é posicionamento — é o que todo mundo já diz estar fazendo.

### 2. Web sem notificação é o pior dos mundos

A LicitaCerta é WhatsApp e nada mais. A VouLicitar e a Alerta Licitação têm app
com push. O Radar hoje tem site e CLI: o usuário precisa **lembrar de entrar**.

O problema original que você escreveu no escopo era "quem esquece de olhar,
perde o prazo". A versão web, do jeito que está, não resolve isso — ela troca
o site do PNCP por um site mais bonito, e mantém a obrigação de lembrar. O
canal de saída não é um item de roadmap; é metade do produto.

## O norte que os dados sugerem

Existe um recorte que nenhum dos sete está ocupando, e ele apareceu na pesquisa
sobre MEI:

- Licitações de até R$ 80.000 são **exclusivas** para ME e EPP: empresa grande
  não pode nem participar.
- Mais de 70% dos editais de dispensa eletrônica no PNCP em 2026 são exclusivos
  ME/EPP.
- A dispensa de pequeno valor (até R$ 10.000) é o caminho recomendado para a
  primeira participação: menos exigência documental, e serve para acumular
  atestado de capacidade técnica.
- O teto do MEI é R$ 81 mil/ano — contrato acima disso desenquadra o regime, ou
  seja, licitação grande não é só difícil para ele, é **prejudicial**.

Todos os concorrentes vendem "todas as licitações do Brasil" e deixam o usuário
filtrar. Para quem nunca licitou, isso é o problema, não a solução: a maior
parte do que ele vê é coisa que ele não pode ou não deveria disputar.

> **Proposta de norte:** o Radar não é um buscador de licitações. É a ferramenta
> da **primeira** licitação — dispensa eletrônica e pregão de pequeno valor,
> exclusivos ME/EPP, no PNCP.

O que isso ganha:

- **Vira virtude o que hoje é limitação.** Usar só o PNCP deixa de ser cobertura
  menor e passa a ser a fonte certa: dispensa eletrônica vive lá, por obrigação
  da Lei 14.133.
- **Justifica o recorte que você já fez.** RJ e teto de R$ 250 mil deixam de ser
  "escopo pequeno para começar" e viram a tese do produto. Aliás, o teto tem um
  número mais defensável: R$ 80 mil, a faixa da exclusividade ME/EPP.
- **Dá uma frase que nenhum concorrente pode copiar sem se contradizer.** Quem
  vende cobertura de 6.000 portais não vai dizer "mostramos menos coisas para
  você, de propósito".
- **O código já está a meio caminho.** `modalidades = [8]` no `contratinho.toml` é
  dispensa; o filtro por valor existe; o recorte por UF existe.

O que isso custa: o mercado endereçável fica menor, e o usuário que der certo
vai embora para uma plataforma completa quando crescer. É um funil de entrada,
não um produto para a vida toda — e isso precisa ser aceito conscientemente.

## O que muda no roadmap, se o norte for aceito

1. **Trocar o teto de R$ 250 mil por R$ 80 mil** no padrão do `contratinho init` e no
   MVP web, com a explicação: acima disso, empresa grande entra na disputa.
2. **Marcar no cartão se o edital é exclusivo ME/EPP.** É a informação que mais
   muda a decisão de quem está começando, e ninguém destaca isso.
3. **Priorizar dispensa eletrônica** na ordenação, não só incluí-la.
4. **Resolver o canal antes de qualquer tela nova.** E-mail resolve; WhatsApp é
   o padrão do segmento e tem custo e burocracia de API. Escolher um e entregar.
5. **Rever a justificativa do `pypncp` no README**, que ficou desatualizada
   depois que o `portal.py` passou a usar a API de busca do portal.

## O que eu não consegui verificar

- Preço de Effecti e ConLicitação: só sob consulta.
- Nenhum teste de uso real: não criei conta em nenhum dos produtos, então
  qualidade de filtro, frequência real de alerta e taxa de falso positivo estão
  fora desta análise. Isso só se descobre assinando um mês de dois deles.
- Número de clientes e faturamento de qualquer um deles: nada confiável é
  público.
- As entrevistas previstas no `PRODUTO.md` continuam sendo o furo maior. Este
  documento mapeia a oferta; ele não prova que existe alguém disposto a pagar.

## Fontes

- https://licitacerta.com.br/
- https://www.voulicitar.com/
- https://alertalicitacao.com.br/
- https://www.contratax.com.br/comparativo
- https://www.licitaja.com.br/
- https://effecti.com.br/plataforma/
- https://conlicitacao.com.br/acompanhar-licitacoes-publicas/
- https://www.contratax.com.br/blog/como-mei-participar-licitacao
- https://licitagov.org/artigos/licitacoes-para-mei-e-pequenas-empresas/
