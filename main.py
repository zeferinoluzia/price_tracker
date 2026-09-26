import csv
from playwright.sync_api import sync_playwright
from scraper import pegar_preco_amazon
from database import criar_banco, salvar_preco


# Criar o banco de dados
criar_banco()


# Ler produtos do CSV
with open("products.csv", "r", encoding="cp1252") as arquivo:
    produtos = list(csv.DictReader(arquivo))


# Lista onde vamos guardar os produtos que tiveram queda
produtos_com_queda = []


with sync_playwright() as p:

    # Abrir UM navegador
    navegador = p.chromium.launch(headless=False)

    # Criar UMA página
    pagina = navegador.new_page()

    print(f"🔎 Verificando {len(produtos)} produtos...")

    # Percorrer todos os produtos
    for produto in produtos:

        nome = produto["nome"]
        url = produto["url"]
        preco_inicial = float(produto["preco_inicial"])

        try:

            # Buscar preço atual
            preco_atual = pegar_preco_amazon(pagina, url)

            # Salvar preço no banco de dados
            salvar_preco(nome, url, preco_atual)

            # Verificar se o preço caiu
            if preco_atual < preco_inicial:

                queda_reais = preco_inicial - preco_atual
                queda_percentual = (queda_reais / preco_inicial) * 100

                # Guardar informações da queda
                produtos_com_queda.append({
                    "nome": nome,
                    "preco_inicial": preco_inicial,
                    "preco_atual": preco_atual,
                    "queda_reais": queda_reais,
                    "queda_percentual": queda_percentual
                })

        except Exception as erro:

            print(f"❌ Erro ao consultar {nome}: {erro}")

    # Fechar o navegador depois de consultar todos os produtos
    navegador.close()


# Mostrar resultados
print()
print("=" * 50)
print("🚨 PREÇOS QUE CAÍRAM")
print("=" * 50)


if len(produtos_com_queda) == 0:

    print("Nenhum produto teve queda de preço.")

else:

    for produto in produtos_com_queda:

        print()
        print(produto["nome"])
        print(f"De: R$ {produto['preco_inicial']:.2f}")
        print(f"Por: R$ {produto['preco_atual']:.2f}")
        print(
            f"Economia: R$ {produto['queda_reais']:.2f} "
            f"({produto['queda_percentual']:.2f}%)"
        )


print()
print("=" * 50)
print("✅ Verificação concluída.")