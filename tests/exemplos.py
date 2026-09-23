"""Configuração usada pelos testes.

Separada de `cfg.EXEMPLO` de propósito: o arquivo que o `contratinho init` gera
acompanha o escopo do momento (hoje, RJ até R$ 250 mil) e vai mudar. Os testes
de filtro, fonte e CLI exercitam o mecanismo, não o escopo — acoplá-los ao
padrão faria cada ajuste de escopo quebrar meia suíte sem nenhum bug junto.
"""

CONFIG_TESTE = """
[radar]
uf = ["SP", "MG"]
valor_minimo = 10000

[[perfil]]
nome = "impressos"
termos = ["impressão", "gráfica", "folder", "cartilha"]
excluir = ["impressora", "toner", "cartucho"]

[[perfil]]
nome = "papel"
termos = ["papel sulfite", "papel offset"]
"""
