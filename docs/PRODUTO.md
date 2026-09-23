# Contratinho: direção do produto

## Público e proposta
Pessoas com renda que desejam começar a fornecer ao governo e pequenos
empreendedores que precisam descobrir oportunidades compatíveis com sua atuação.
O governo é um potencial cliente. O produto não promete renda, habilitação ou vitória.
Não presumimos familiaridade com licitações nem exigimos CNPJ para explorar editais.

## MVP
Criar conta → escolher um mercado e região → consultar oportunidades → acompanhar
editais em uma lista pessoal com etapas: interessado, analisando, preparando e arquivado.
Cada oportunidade mostra órgão, local, valor quando conhecido, fonte e atualização.
Prazos desconhecidos são explícitos. A fonte oficial deve ser conferida antes de participar.

Mercados iniciais são hipóteses editáveis: serviços gráficos, limpeza, manutenção,
informática e alimentação. Correspondência por palavras é explicada, não apresentada
como certificação de aptidão. Estados indicam local da contratação, não esfera do órgão.

## Princípio de experiência

Cada tela deve ajudar o usuário a responder: o que o órgão quer, se combina com seu
negócio, quanto vale, qual é o prazo, o que conferir e onde está a fonte oficial. A
interface pública usa cartões de decisão e linguagem cotidiana; tabelas e identificadores
técnicos ficam em segundo plano. A análise de concorrentes e a direção visual estão em
`docs/REFERENCIAS_UX.md`.

## Métricas de validação
- Ativação: proporção de contas que configuram mercado e salvam um edital.
- Tempo até o primeiro edital acompanhado.
- Retorno semanal e oportunidades marcadas como irrelevantes (próxima etapa).
- Frescor da coleta, falhas e cobertura: acompanhar antes do lançamento.
Metas numéricas serão definidas após entrevistas e piloto; ainda não há validação comercial.

## Fora desta primeira entrega
Pagamento, envio automático de propostas, recomendações jurídicas, decisão automática de
habilitação, marketplace e microserviços.

O aviso por e-mail **saiu** desta lista em 23/09/2026: um site que exige lembrar de
entrar não resolve o problema que abriu o projeto. Ver `send_alerts` em `docs/WEB.md`.
WhatsApp segue fora até haver usuário validado — é o padrão do segmento, com custo e
burocracia de API que só se pagam depois.

O que o produto promete e o que ele explicitamente não promete está em `docs/CONTRATO.md`.
