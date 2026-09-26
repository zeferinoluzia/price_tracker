import sqlite3
from datetime import datetime


def criar_banco():

    conexao = sqlite3.connect("prices.db")

    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            url TEXT,
            preco REAL,
            data_hora TEXT
        )
    """)

    conexao.commit()
    conexao.close()


def salvar_preco(nome, url, preco):

    conexao = sqlite3.connect("prices.db")

    cursor = conexao.cursor()

    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO historico_precos
        (nome, url, preco, data_hora)
        VALUES (?, ?, ?, ?)
    """, (nome, url, preco, data_hora))

    conexao.commit()
    conexao.close()


def buscar_ultimo_preco(nome):

    conexao = sqlite3.connect("prices.db")
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT preco
        FROM historico_precos
        WHERE nome = ?
        ORDER BY data_hora DESC
        LIMIT 1
    """, (nome,))

    resultado = cursor.fetchone()

    conexao.close()

    if resultado is None:
        return None

    return resultado[0]