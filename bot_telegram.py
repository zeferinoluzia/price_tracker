import csv
import os
import sqlite3
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
# ==================================================
# CONFIGURAÇÕES
# ==================================================
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "products.csv"
DB_PATH = BASE_DIR / "prices.db"
load_dotenv(BASE_DIR / ".env")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ITENS_POR_PAGINA = 8
NOME, URL, PRECO = range(3)
# ==================================================
# BANCO DE DADOS
# ==================================================
def conectar_banco():
    return sqlite3.connect(DB_PATH, timeout=30)
def ultimo_preco(nome):
    with conectar_banco() as con:
        cursor = con.cursor()
        cursor.execute("""
            SELECT preco, data_hora
            FROM historico_precos
            WHERE nome = ?
            ORDER BY data_hora DESC, id DESC
            LIMIT 1
        """, (nome,))
        return cursor.fetchone()
def estatisticas(nome):
    with conectar_banco() as con:
        cursor = con.cursor()
        cursor.execute("""
            SELECT
                MIN(preco),
                MAX(preco),
                AVG(preco),
                COUNT(*)
            FROM historico_precos
            WHERE nome = ?
        """, (nome,))
        return cursor.fetchone()
def menor_preco_historico(nome):
    with conectar_banco() as con:
        cursor = con.cursor()
        cursor.execute("""
            SELECT MIN(preco)
            FROM historico_precos
            WHERE nome = ?
        """, (nome,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
def salvar_preco(nome, url, preco):
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conectar_banco() as con:
        con.execute("""
            INSERT INTO historico_precos
            (nome, url, preco, data_hora)
            VALUES (?, ?, ?, ?)
        """, (nome, url, preco, data_hora))
# ==================================================
# PRODUTOS E CSV
# ==================================================
def carregar_produtos():
    if not CSV_PATH.exists():
        return []
    with open(
        CSV_PATH,
        "r",
        encoding="cp1252",
        newline=""
    ) as arquivo:
        return list(csv.DictReader(arquivo))
def salvar_produtos(produtos):
    temporario = CSV_PATH.with_suffix(".tmp")
    with open(
        temporario,
        "w",
        encoding="cp1252",
        newline=""
    ) as arquivo:
        campos = ["nome", "url", "preco_inicial"]
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=campos
        )
        escritor.writeheader()
        escritor.writerows(produtos)
    os.replace(temporario, CSV_PATH)
def formatar_preco(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
def validar_url(url):
    try:
        dominio = (urlparse(url).hostname or "").lower()
        return (
            dominio == "amzn.to"
            or dominio == "amazon.com.br"
            or dominio.endswith(".amazon.com.br")
            or dominio == "amazon.com"
            or dominio.endswith(".amazon.com")
        )
    except Exception:
        return False
# ==================================================
# MENU PRINCIPAL
# ==================================================
def teclado_principal():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📦 Meus produtos",
                callback_data="products:0"
            ),
            InlineKeyboardButton(
                "📈 Histórico",
                callback_data="history:0"
            ),
        ],
        [
            InlineKeyboardButton(
                "➕ Adicionar produto",
                callback_data="add"
            ),
            InlineKeyboardButton(
                "🗑️ Remover produto",
                callback_data="remove:0"
            ),
        ],
        [
            InlineKeyboardButton(
                "📉 Menores preços",
                callback_data="lowest"
            ),
        ],
    ])
async def mostrar_menu(update, context):
    texto = (
        "🏠 CASA NOVA — RASTREADOR DE PREÇOS\n\n"
        "O que tu deseja fazer?"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            texto,
            reply_markup=teclado_principal()
        )
    else:
        await update.message.reply_text(
            texto,
            reply_markup=teclado_principal()
        )
async def abrir_menu_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Abre um novo menu no grupo a partir do botão do alerta."""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "🏠 CASA NOVA — RASTREADOR DE PREÇOS\n\n"
        "O que tu deseja fazer?",
        reply_markup=teclado_principal()
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await mostrar_menu(update, context)
async def voltar_menu(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏠 Menu principal\n\nEscolhe uma opção:",
        reply_markup=teclado_principal()
    )
# ==================================================
# LISTAR PRODUTOS
# ==================================================
async def listar_produtos_callback(update, context):
    query = update.callback_query
    await query.answer()
    produtos = carregar_produtos()
    pagina = int(query.data.split(":")[1])
    if not produtos:
        await query.edit_message_text(
            "Não há produtos cadastrados.",
            reply_markup=teclado_principal()
        )
        return
    inicio = pagina * ITENS_POR_PAGINA
    fim = min(inicio + ITENS_POR_PAGINA, len(produtos))
    linhas = ["📦 PRODUTOS MONITORADOS\n"]
    teclado = []
    for indice in range(inicio, fim):
        produto = produtos[indice]
        resultado = ultimo_preco(produto["nome"])
        if resultado:
            preco = formatar_preco(resultado[0])
            linhas.append(
                f"{indice + 1}. {produto['nome']}\n"
                f"💰 {preco}"
            )
        else:
            linhas.append(
                f"{indice + 1}. {produto['nome']}\n"
                "⏳ Sem preço registrado"
            )
        teclado.append([
            InlineKeyboardButton(
                f"🛒 {produto['nome'][:45]}",
                url=produto["url"]
            )
        ])
    total_paginas = (
        (len(produtos) - 1) // ITENS_POR_PAGINA + 1
    )
    linhas.append(
        f"\nPágina {pagina + 1} de {total_paginas}"
    )
    navegacao = []
    if pagina > 0:
        navegacao.append(
            InlineKeyboardButton(
                "⬅️ Anterior",
                callback_data=f"products:{pagina - 1}"
            )
        )
    if fim < len(produtos):
        navegacao.append(
            InlineKeyboardButton(
                "Próxima ➡️",
                callback_data=f"products:{pagina + 1}"
            )
        )
    if navegacao:
        teclado.append(navegacao)
    teclado.append([
        InlineKeyboardButton(
            "🏠 Menu",
            callback_data="home"
        )
    ])
    await query.edit_message_text(
        "\n\n".join(linhas),
        reply_markup=InlineKeyboardMarkup(teclado)
    )
# ==================================================
# HISTÓRICO DE PREÇOS
# ==================================================
async def abrir_historico(update, context):
    query = update.callback_query
    await query.answer()
    produtos = carregar_produtos()
    if not produtos:
        await query.edit_message_text(
            "Não há produtos cadastrados.",
            reply_markup=teclado_principal()
        )
        return
    pagina = int(query.data.split(":")[1])
    inicio = pagina * ITENS_POR_PAGINA
    fim = min(inicio + ITENS_POR_PAGINA, len(produtos))
    teclado = []
    for indice in range(inicio, fim):
        produto = produtos[indice]
        teclado.append([
            InlineKeyboardButton(
                produto["nome"][:55],
                callback_data=f"histitem:{indice}"
            )
        ])
    navegacao = []
    if pagina > 0:
        navegacao.append(
            InlineKeyboardButton(
                "⬅️ Anterior",
                callback_data=f"history:{pagina - 1}"
            )
        )
    if fim < len(produtos):
        navegacao.append(
            InlineKeyboardButton(
                "Próxima ➡️",
                callback_data=f"history:{pagina + 1}"
            )
        )
    if navegacao:
        teclado.append(navegacao)
    teclado.append([
        InlineKeyboardButton(
            "🏠 Menu",
            callback_data="home"
        )
    ])
    await query.edit_message_text(
        "📈 Escolhe um produto para consultar o histórico:",
        reply_markup=InlineKeyboardMarkup(teclado)
    )
async def selecionar_historico(update, context):
    query = update.callback_query
    await query.answer()
    indice = int(query.data.split(":")[1])
    produtos = carregar_produtos()
    if indice >= len(produtos):
        await query.edit_message_text(
            "A lista mudou. Abre o histórico novamente.",
            reply_markup=teclado_principal()
        )
        return
    produto = produtos[indice]
    nome = produto["nome"]
    url = produto["url"]
    with conectar_banco() as con:
        cursor = con.cursor()
        cursor.execute("""
            SELECT preco, data_hora
            FROM historico_precos
            WHERE nome = ?
            ORDER BY data_hora DESC, id DESC
            LIMIT 10
        """, (nome,))
        registros = cursor.fetchall()
    menor, maior, media, total = estatisticas(nome)
    linhas = [
        f"📈 HISTÓRICO\n\n📦 {nome}\n"
    ]
    if not registros:
        linhas.append("Nenhum registro encontrado.")
    else:
        linhas.append("Últimos registros:")
        for preco, data_hora in registros:
            linhas.append(
                f"• {data_hora}: {formatar_preco(preco)}"
            )
        linhas.extend([
            "",
            f"🔻 Menor: {formatar_preco(menor)}",
            f"🔺 Maior: {formatar_preco(maior)}",
            f"📊 Média: {formatar_preco(media)}",
            f"🧾 Total de registros: {total}",
        ])
    await query.edit_message_text(
        "\n".join(linhas),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🛒 Ver na Amazon",
                    url=url
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Voltar",
                    callback_data="history:0"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏠 Menu",
                    callback_data="home"
                )
            ]
        ])
    )
# ==================================================
# MENORES PREÇOS
# ==================================================
async def menores_precos(update, context):
    query = update.callback_query
    await query.answer()
    produtos = carregar_produtos()
    resultados = []
    for produto in produtos:
        atual = ultimo_preco(produto["nome"])
        minimo = menor_preco_historico(produto["nome"])
        if atual and minimo is not None:
            resultados.append({
                "nome": produto["nome"],
                "atual": atual[0],
                "minimo": minimo,
                "url": produto["url"]
            })
    resultados.sort(key=lambda item: item["minimo"])
    if not resultados:
        await query.edit_message_text(
            "Ainda não há preços registrados.",
            reply_markup=teclado_principal()
        )
        return
    linhas = ["📉 MENORES PREÇOS HISTÓRICOS\n"]
    teclado = []
    for item in resultados[:15]:
        linhas.append(
            f"📦 {item['nome']}\n"
            f"🔻 Mínimo: {formatar_preco(item['minimo'])}\n"
            f"💰 Atual: {formatar_preco(item['atual'])}"
        )
        teclado.append([
            InlineKeyboardButton(
                f"🛒 {item['nome'][:45]}",
                url=item["url"]
            )
        ])
    teclado.append([
        InlineKeyboardButton(
            "🏠 Menu",
            callback_data="home"
        )
    ])
    await query.edit_message_text(
        "\n\n".join(linhas),
        reply_markup=InlineKeyboardMarkup(teclado)
    )
# ==================================================
# ADICIONAR PRODUTO
# ==================================================
async def iniciar_adicao(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "➕ ADICIONAR PRODUTO\n\n"
        "Envia o nome do produto:\n\n"
        "Para cancelar, digita /cancelar."
    )
    return NOME
async def receber_nome(update, context):
    nome = update.message.text.strip()
    if not nome:
        await update.message.reply_text(
            "O nome não pode ficar vazio. Tenta novamente:"
        )
        return NOME
    produtos = carregar_produtos()
    if any(
        p["nome"].strip().lower() == nome.lower()
        for p in produtos
    ):
        await update.message.reply_text(
            "Já existe um produto com esse nome. "
            "Envia outro nome:"
        )
        return NOME
    context.user_data["novo_produto"] = {
        "nome": nome
    }
    await update.message.reply_text(
        "Agora envia o link do produto na Amazon:"
    )
    return URL
async def receber_url(update, context):
    url = update.message.text.strip()
    if not validar_url(url):
        await update.message.reply_text(
            "Esse link não parece ser da Amazon.\n\n"
            "Envia um link válido da Amazon ou um link curto amzn.to:"
        )
        return URL
    context.user_data["novo_produto"]["url"] = url
    await update.message.reply_text(
        "Qual é o preço atual do produto?\n\n"
        "Exemplo: 249,90"
    )
    return PRECO
async def receber_preco(update, context):
    texto = update.message.text.strip()
    texto = texto.replace(".", "").replace(",", ".")
    try:
        preco = float(texto)
        if preco <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "Preço inválido.\n"
            "Envia um valor positivo, como 249,90:"
        )
        return PRECO
    produto = context.user_data["novo_produto"]
    produto["preco_inicial"] = f"{preco:.2f}"
    produtos = carregar_produtos()
    produtos.append(produto)
    try:
        salvar_produtos(produtos)
        salvar_preco(
            produto["nome"],
            produto["url"],
            preco
        )
    except Exception as erro:
        await update.message.reply_text(
            f"Não consegui salvar o produto: {erro}"
        )
        return ConversationHandler.END
    await update.message.reply_text(
        f"✅ Produto adicionado!\n\n"
        f"📦 {produto['nome']}\n"
        f"💰 Preço inicial: {formatar_preco(preco)}\n\n"
        f"🛒 Link: {produto['url']}",
        reply_markup=teclado_principal()
    )
    context.user_data.pop("novo_produto", None)
    return ConversationHandler.END
async def cancelar_adicao(update, context):
    context.user_data.pop("novo_produto", None)
    await update.message.reply_text(
        "Cadastro cancelado.",
        reply_markup=teclado_principal()
    )
    return ConversationHandler.END
# ==================================================
# REMOVER PRODUTO
# ==================================================
async def abrir_remocao(update, context):
    query = update.callback_query
    await query.answer()
    produtos = carregar_produtos()
    if not produtos:
        await query.edit_message_text(
            "Não há produtos cadastrados.",
            reply_markup=teclado_principal()
        )
        return
    pagina = int(query.data.split(":")[1])
    inicio = pagina * ITENS_POR_PAGINA
    fim = min(inicio + ITENS_POR_PAGINA, len(produtos))
    teclado = []
    for indice in range(inicio, fim):
        produto = produtos[indice]
        teclado.append([
            InlineKeyboardButton(
                produto["nome"][:55],
                callback_data=f"rmitem:{indice}"
            )
        ])
    navegacao = []
    if pagina > 0:
        navegacao.append(
            InlineKeyboardButton(
                "⬅️ Anterior",
                callback_data=f"remove:{pagina - 1}"
            )
        )
    if fim < len(produtos):
        navegacao.append(
            InlineKeyboardButton(
                "Próxima ➡️",
                callback_data=f"remove:{pagina + 1}"
            )
        )
    if navegacao:
        teclado.append(navegacao)
    teclado.append([
        InlineKeyboardButton(
            "🏠 Menu",
            callback_data="home"
        )
    ])
    await query.edit_message_text(
        "🗑️ Escolhe o produto que deseja remover:",
        reply_markup=InlineKeyboardMarkup(teclado)
    )
async def escolher_remocao(update, context):
    query = update.callback_query
    await query.answer()
    indice = int(query.data.split(":")[1])
    produtos = carregar_produtos()
    if indice >= len(produtos):
        await query.edit_message_text(
            "A lista mudou. Abre a remoção novamente.",
            reply_markup=teclado_principal()
        )
        return
    produto = produtos[indice]
    context.user_data["remover_produto"] = produto
    await query.edit_message_text(
        f"Tem certeza que deseja remover?\n\n"
        f"📦 {produto['nome']}\n\n"
        "O histórico de preços será preservado.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Confirmar",
                    callback_data="confirm_remove"
                ),
                InlineKeyboardButton(
                    "❌ Cancelar",
                    callback_data="cancel_remove"
                )
            ]
        ])
    )
async def confirmar_remocao(update, context):
    query = update.callback_query
    await query.answer()
    produto = context.user_data.pop(
        "remover_produto",
        None
    )
    if not produto:
        await query.edit_message_text(
            "Não há produto selecionado.",
            reply_markup=teclado_principal()
        )
        return
    produtos = carregar_produtos()
    produtos = [
        p for p in produtos
        if not (
            p["nome"] == produto["nome"]
            and p["url"] == produto["url"]
        )
    ]
    salvar_produtos(produtos)
    await query.edit_message_text(
        f"✅ {produto['nome']} foi removido do acompanhamento.\n\n"
        "ℹ️ O histórico foi mantido.",
        reply_markup=teclado_principal()
    )
async def cancelar_remocao(update, context):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("remover_produto", None)
    await query.edit_message_text(
        "Remoção cancelada.",
        reply_markup=teclado_principal()
    )
# ==================================================
# INICIALIZAÇÃO
# ==================================================
def main():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN não encontrado no arquivo .env"
        )
    app = Application.builder().token(TOKEN).build()
    cadastro = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                iniciar_adicao,
                pattern="^add$"
            )
        ],
        states={
            NOME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receber_nome
                )
            ],
            URL: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receber_url
                )
            ],
            PRECO: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receber_preco
                )
            ],
        },
        fallbacks=[
            CommandHandler(
                "cancelar",
                cancelar_adicao
            )
        ],
        per_chat=True,
        per_user=True,
    )
    app.add_handler(cadastro)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(
        CallbackQueryHandler(
            abrir_menu_alerta,
            pattern="^open_menu$"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            voltar_menu,
            pattern="^home$"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            listar_produtos_callback,
            pattern="^products:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            abrir_historico,
            pattern="^history:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            selecionar_historico,
            pattern="^histitem:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            menores_precos,
            pattern="^lowest$"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            abrir_remocao,
            pattern="^remove:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            escolher_remocao,
            pattern="^rmitem:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            confirmar_remocao,
            pattern="^confirm_remove$"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            cancelar_remocao,
            pattern="^cancel_remove$"
        )
    )
    print("🤖 Bot Telegram iniciado!")
    app.run_polling()
if __name__ == "__main__":
    main()
