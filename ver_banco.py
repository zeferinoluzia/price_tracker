import sqlite3
import csv


# Ler produtos do CSV
with open("products.csv", "r", encoding="cp1252") as arquivo:
    produtos = list(csv.DictReader(arquivo))


def listar_produtos():

    print()
    print("=" * 50)
    print("PRODUTOS")
    print("=" * 50)

    for i, produto in enumerate(produtos, start=1):
        print(f"{i:2} - {produto['nome']}")


def selecionar_produto():

    listar_produtos()

    escolha = input("\nDigite o número ou o nome do produto: ").strip()

    # Se digitou um número
    if escolha.isdigit():

        numero = int(escolha)

        if 1 <= numero <= len(produtos):
            return produtos[numero - 1]

        print("❌ Número inválido.")
        return None

    # Se digitou o nome
    for produto in produtos:

        if produto["nome"].strip().lower() == escolha.lower():
            return produto

    print("❌ Produto não encontrado.")
    return None


def ver_historico():

    produto = selecionar_produto()

    if produto is None:
        return

    nome = produto["nome"]

    conexao = sqlite3.connect("prices.db")
    cursor = conexao.cursor()

    # Buscar todo o histórico
    cursor.execute("""
        SELECT preco, data_hora
        FROM historico_precos
        WHERE nome = ?
        ORDER BY data_hora
    """, (nome,))

    registros = cursor.fetchall()

    # Buscar estatísticas
    cursor.execute("""
        SELECT
            MIN(preco),
            MAX(preco),
            AVG(preco)
        FROM historico_precos
        WHERE nome = ?
    """, (nome,))

    estatisticas = cursor.fetchone()

    conexao.close()

    print()
    print("=" * 60)
    print(f"HISTÓRICO: {nome}")
    print("=" * 60)

    if not registros:

        print("Nenhum histórico encontrado.")
        return

    # Mostrar registros
    print()
    print(f"{'Data':<20} {'Preço':>15}")
    print("-" * 60)

    for preco, data_hora in registros:

        print(
            f"{data_hora:<20} "
            f"R$ {preco:>10.2f}"
        )

    # Estatísticas
    menor_preco = estatisticas[0]
    maior_preco = estatisticas[1]
    preco_medio = estatisticas[2]

    print()
    print("-" * 60)
    print(f"Menor preço:     R$ {menor_preco:.2f}")
    print(f"Maior preço:     R$ {maior_preco:.2f}")
    print(f"Preço médio:     R$ {preco_medio:.2f}")


def ver_produto_atual():

    # Escolhe o produto UMA única vez
    produto = selecionar_produto()

    if produto is None:
        return

    nome = produto["nome"]
    preco_inicial = float(produto["preco_inicial"])

    # Buscar último preço no banco
    conexao = sqlite3.connect("prices.db")
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT preco, data_hora
        FROM historico_precos
        WHERE nome = ?
        ORDER BY data_hora DESC
        LIMIT 1
    """, (nome,))

    resultado = cursor.fetchone()
    # Buscar estatísticas do histórico
    cursor.execute("""
    SELECT
        MIN(preco),
        MAX(preco),
        AVG(preco)
    FROM historico_precos
    WHERE nome = ?
    """, (nome,))

    estatisticas = cursor.fetchone()

    conexao.close()

    print()
    print("=" * 50)
    print(f"PRODUTO: {nome}")
    print("=" * 50)

    # Produto ainda não foi consultado pelo bot
    if resultado is None:

        print("❌ Esse produto ainda não possui preço no banco.")
        return

    preco_atual = resultado[0]
    data_hora = resultado[1]
    menor_preco = estatisticas[0]
    maior_preco = estatisticas[1]
    preco_medio = estatisticas[2]

    print()
    print(f"Preço inicial:   R$ {preco_inicial:.2f}")
    print(f"Preço atual:     R$ {preco_atual:.2f}")
    print(f"Última consulta: {data_hora}")
    print()
    print(f"Menor preço:     R$ {menor_preco:.2f}")
    print(f"Maior preço:     R$ {maior_preco:.2f}")
    print(f"Preço médio:     R$ {preco_medio:.2f}")

    # Comparação
    if preco_atual < preco_inicial:

        queda = preco_inicial - preco_atual
        percentual = (queda / preco_inicial) * 100

        print()
        print(f"📉 Queda: R$ {queda:.2f}")
        print(f"📊 Percentual: {percentual:.2f}%")

    elif preco_atual > preco_inicial:

        aumento = preco_atual - preco_inicial
        percentual = (aumento / preco_inicial) * 100

        print()
        print(f"📈 Aumento: R$ {aumento:.2f}")
        print(f"📊 Percentual: {percentual:.2f}%")

    else:

        print()
        print("➡️ O preço está igual ao preço inicial.")


def main():

    while True:

        print()
        print("=" * 50)
        print("PRICE TRACKER")
        print("=" * 50)

        print()
        print("1 - Ver histórico de preços")
        print("2 - Ver produto atual")
        print("3 - Listar produtos")
        print("0 - Sair")

        escolha = input("\nDigite uma opção: ").strip()

        if escolha == "1":

            ver_historico()

        elif escolha == "2":

            ver_produto_atual()

        elif escolha == "3":

            listar_produtos()

        elif escolha == "0":

            print("\n👋 Saindo...")
            break

        else:

            print("\n❌ Opção inválida.")


main()