import csv
import os
import json
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from scraper import pegar_preco_amazon
from database import criar_banco, salvar_preco, buscar_ultimo_preco


# ==================================================
# CONFIGURAÇÕES
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TELEGRAM_ALERT_CHAT_ID = os.getenv(
    "TELEGRAM_ALERT_CHAT_ID",
    TELEGRAM_CHAT_ID
).strip()


# ==================================================
# TELEGRAM
# ==================================================

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN:
        print("⚠️ Token do Telegram não configurado.")
        return False

    if not TELEGRAM_ALERT_CHAT_ID:
        print("⚠️ Chat ID de destino não configurado.")
        return False

    print(f"📨 Destino do alerta: {TELEGRAM_ALERT_CHAT_ID}")

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    teclado = {
        "inline_keyboard": [[
            {"text": "📋 Abrir menu", "callback_data": "open_menu"}
        ]]
    }
    dados = urllib.parse.urlencode({
        "chat_id": TELEGRAM_ALERT_CHAT_ID,
        "text": mensagem,
        "reply_markup": json.dumps(teclado, ensure_ascii=False)
    }).encode("utf-8")

    requisicao = urllib.request.Request(
        url,
        data=dados,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(requisicao, timeout=30) as resposta:
            resultado = json.loads(
                resposta.read().decode("utf-8", errors="replace")
            )

        if resultado.get("ok"):
            print("📲 Alerta enviado pelo Telegram!")
            return True

        print("⚠️ Telegram não confirmou o envio:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        return False

    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", errors="replace")
        print(f"❌ Erro HTTP {erro.code} ao enviar mensagem pelo Telegram.")
        try:
            print(json.dumps(json.loads(detalhe), indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(detalhe)
        return False

    except urllib.error.URLError as erro:
        print(f"❌ Erro de conexão com o Telegram: {erro.reason}")
        return False

    except Exception as erro:
        print(f"❌ Erro inesperado no Telegram: {erro}")
        return False


# ==================================================
# INICIALIZAÇÃO DO BANCO
# ==================================================

criar_banco()


# ==================================================
# LER PRODUTOS
# ==================================================

with open(BASE_DIR / "products.csv", "r", encoding="cp1252", newline="") as arquivo:
    produtos = list(csv.DictReader(arquivo))


# ==================================================
# MONITORAMENTO DE PREÇOS
# ==================================================

produtos_com_queda = []

print("=" * 50)
print("🚀 INICIANDO RASTREADOR DE PREÇOS")
print("=" * 50)
print(f"📁 Pasta do projeto: {BASE_DIR}")
print(f"📦 Produtos cadastrados: {len(produtos)}")
print(f"📨 Destino dos alertas: {TELEGRAM_ALERT_CHAT_ID or 'não configurado'}")

with sync_playwright() as p:
    navegador = p.chromium.launch(
        channel="msedge",
        headless=False
    )
    pagina = navegador.new_page()

    print(f"🔎 Verificando {len(produtos)} produtos...")

    for produto in produtos:
        nome = produto["nome"].strip()
        url = produto["url"].strip()

        try:
            print(f"\n🔍 Consultando: {nome}")
            preco_anterior = buscar_ultimo_preco(nome)
            preco_atual = pegar_preco_amazon(pagina, url)

            if preco_atual is None or preco_atual <= 0:
                print("⚠️ Preço inválido. Produto ignorado.")
                continue

            print(f"💰 Preço atual: R$ {preco_atual:.2f}")

            if preco_anterior is not None and preco_anterior > 0:
                print(f"📊 Preço anterior: R$ {preco_anterior:.2f}")

                if preco_atual < preco_anterior:
                    queda_reais = preco_anterior - preco_atual
                    queda_percentual = (queda_reais / preco_anterior) * 100

                    if queda_percentual >= 20:
                        dados_queda = {
                            "nome": nome,
                            "preco_anterior": preco_anterior,
                            "preco_atual": preco_atual,
                            "queda_reais": queda_reais,
                            "queda_percentual": queda_percentual,
                            "url": url
                        }
                        produtos_com_queda.append(dados_queda)

                        print("\n🚨 ALERTA DE PREÇO!")
                        print(f"Produto: {nome}")
                        print(f"Anterior: R$ {preco_anterior:.2f}")
                        print(f"Atual:    R$ {preco_atual:.2f}")
                        print(f"Queda:    {queda_percentual:.2f}%")

                        mensagem = (
                            "🚨 QUEDA DE PREÇO DETECTADA!\n\n"
                            f"📦 {nome}\n\n"
                            f"💰 Preço anterior: R$ {preco_anterior:.2f}\n"
                            f"🔥 Preço atual: R$ {preco_atual:.2f}\n"
                            f"📉 Queda: {queda_percentual:.2f}%\n"
                            f"💸 Economia: R$ {queda_reais:.2f}\n\n"
                            f"🔗 Ver produto:\n{url}"
                        )
                        enviado = enviar_telegram(mensagem)
                        if not enviado:
                            print("⚠️ A queda foi detectada, mas o alerta não foi enviado.")
                else:
                    print("ℹ️ Não houve queda de preço.")
            else:
                print("ℹ️ Primeiro registro do produto; sem preço anterior para comparar.")

            salvar_preco(nome, url, preco_atual)

        except Exception as erro:
            print(f"❌ Erro ao consultar {nome}: {erro}")

    navegador.close()


# ==================================================
# RESULTADOS
# ==================================================

print("\n" + "=" * 50)
print("🚨 QUEDAS DE 20% OU MAIS")
print("=" * 50)

if not produtos_com_queda:
    print("Nenhum produto teve queda de 20% ou mais.")
else:
    for produto in produtos_com_queda:
        print(f"\n{produto['nome']}")
        print(f"De: R$ {produto['preco_anterior']:.2f}")
        print(f"Por: R$ {produto['preco_atual']:.2f}")
        print(
            f"Economia: R$ {produto['queda_reais']:.2f} "
            f"({produto['queda_percentual']:.2f}%)"
        )

print("\n" + "=" * 50)
print("✅ Verificação concluída.")
