import os
import urllib.request
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

mensagem = (
    "🚨 QUEDA DE PREÇO DETECTADA!\n\n"
    "📦 Produto de teste\n"
    "💰 Preço anterior: R$ 250,00\n"
    "🔥 Preço atual: R$ 190,00\n"
    "📉 Queda: 24%\n"
    "💸 Economia: R$ 60,00\n\n"
    "🔗 https://www.amazon.com.br/"
)

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

dados = urllib.parse.urlencode({
    "chat_id": CHAT_ID,
    "text": mensagem
}).encode("utf-8")

requisicao = urllib.request.Request(url, data=dados)

with urllib.request.urlopen(requisicao, timeout=20) as resposta:
    print(resposta.read().decode("utf-8"))