import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("Token não encontrado no arquivo .env")

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

with urllib.request.urlopen(url) as resposta:
    dados = json.loads(resposta.read().decode("utf-8"))

if dados.get("ok") and dados.get("result"):
    for update in dados["result"]:
        mensagem = update.get("message", {})
        chat = mensagem.get("chat", {})
        if chat:
            print("Chat ID:", chat["id"])
else:
    print("Nenhuma mensagem encontrada. Envie /start ao bot e tente novamente.")