from django.db import migrations

MARKETS = [
    (
        "graficos",
        "Serviços gráficos",
        ["impressão", "gráfica", "cartilha", "folder"],
        ["impressora", "toner", "cartucho"],
    ),
    ("limpeza", "Limpeza e conservação", ["limpeza", "conservação", "higienização"], []),
    (
        "manutencao",
        "Manutenção e pequenos reparos",
        ["manutenção predial", "pintura", "reparo"],
        [],
    ),
    ("informatica", "Informática e suporte", ["informática", "computador", "suporte técnico"], []),
    ("alimentacao", "Alimentação", ["refeição", "alimentação", "lanche", "coffee break"], []),
]


def seed(apps, schema_editor):
    market = apps.get_model("web", "Market")
    for slug, name, terms, exclusions in MARKETS:
        market.objects.using(schema_editor.connection.alias).get_or_create(
            slug=slug, defaults={"name": name, "terms": terms, "exclusions": exclusions}
        )


class Migration(migrations.Migration):
    dependencies = [("web", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
