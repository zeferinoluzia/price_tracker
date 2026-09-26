import csv
from playwright.sync_api import sync_playwright
from scraper import pegar_preco_amazon
from database import criar_banco, salvar_preco, buscar_ultimo_preco


# Criar o banco de dados
criar_banco()


# Ler produtos do CSV
with open("products.csv", "r", encoding="cp1252") as arquivo:
    produtos = list(csv.DictReader(arquivo))


# Lista onde vamos guardar os produtos
# que tiveram queda de pelo menos 20%
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

        try:

            # Buscar o último preço registrado no banco
            preco_anterior = buscar_ultimo_preco(nome)

            # Buscar preço atual na Amazon
            preco_atual = pegar_preco_amazon(pagina, url)

            # Verificar se existe um preço anterior
            if preco_anterior is not None:

                # Verificar se o preço caiu
                if preco_atual < preco_anterior:

                    queda_reais = preco_anterior - preco_atual

                    queda_percentual = (
                        queda_reais / preco_anterior
                    ) * 100

                    # Só considerar quedas de 20% ou mais
                    if queda_percentual >= 20:

                        produtos_com_queda.append({
                            "nome": nome,
                            "preco_anterior": preco_anterior,
                            "preco_atual": preco_atual,
                            "queda_reais": queda_reais,
                            "queda_percentual": queda_percentual
                        })

                        print()
                        print("🚨 ALERTA DE PREÇO!")
                        print(f"Produto: {nome}")
                        print(f"Anterior: R$ {preco_anterior:.2f}")
                        print(f"Atual:    R$ {preco_atual:.2f}")
                        print(f"Queda:    {queda_percentual:.2f}%")

            # Salvar o novo preço no banco
            salvar_preco(nome, url, preco_atual)

        except Exception as erro:

            print(f"❌ Erro ao consultar {nome}: {erro}")

    # Fechar o navegador
    navegador.close()


# Mostrar resultados
print()
print("=" * 50)
print("🚨 QUEDAS DE 20% OU MAIS")
print("=" * 50)


if len(produtos_com_queda) == 0:

    print("Nenhum produto teve queda de 20% ou mais.")

else:

    for produto in produtos_com_queda:

        print()
        print(produto["nome"])
        print(f"De: R$ {produto['preco_anterior']:.2f}")
        print(f"Por: R$ {produto['preco_atual']:.2f}")
        print(
            f"Economia: R$ {produto['queda_reais']:.2f} "
            f"({produto['queda_percentual']:.2f}%)"
        )


print()
print("=" * 50)
print("✅ Verificação concluída.")