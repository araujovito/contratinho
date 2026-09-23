"""Preenche as exclusões dos mercados que nasceram sem nenhuma.

Só o mercado de gráficos tinha lista de exclusão; os outros quatro ficaram
vazios, e o resultado apareceu na primeira tela: uma impressora de cartões
entrou em "Limpeza e conservação" por causa de "rolete de limpeza contínua", e
a mesma impressora entrou em "Alimentação" por "alimentação automática de
cartões".

Cada termo abaixo saiu de um falso positivo observado nos 539 editais coletados
do RJ em 23/09/2026 — nenhum é hipótese.
"""

from django.db import migrations

# slug -> exclusões a aplicar
EXCLUSOES = {
    "limpeza": [
        # impressora de cartões entrou por "rolete de limpeza contínua"
        "impressora",
        "toner",
        "cartucho",
        "rolete",
        # ICMBio e Parque da Tijuca entraram por "Unidades de Conservação"
        "unidade de conservação",
        "conservação ambiental",
    ],
    "manutencao": [
        # "REPAROS E CONSERTOS DE PNEUS" não é manutenção predial
        "pneu",
        "veicular",
        "frota",
    ],
    "alimentacao": [
        # o sentido elétrico/mecânico de "alimentação", que domina em edital
        "alimentação automática",
        "alimentação elétrica",
        "fonte de alimentação",
    ],
}


def aplicar(apps, schema_editor):
    market = apps.get_model("web", "Market")
    banco = schema_editor.connection.alias
    for slug, exclusoes in EXCLUSOES.items():
        # `exclusions=[]` evita sobrescrever ajuste feito no painel de gestão
        market.objects.using(banco).filter(slug=slug, exclusions=[]).update(exclusions=exclusoes)


def desfazer(apps, schema_editor):
    market = apps.get_model("web", "Market")
    banco = schema_editor.connection.alias
    for slug, exclusoes in EXCLUSOES.items():
        market.objects.using(banco).filter(slug=slug, exclusions=exclusoes).update(exclusions=[])


class Migration(migrations.Migration):
    dependencies = [("web", "0005_opportunity_documents_opportunity_enriched_at_and_more")]
    operations = [migrations.RunPython(aplicar, desfazer)]
