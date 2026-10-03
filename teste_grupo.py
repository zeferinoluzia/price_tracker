import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_ALERT_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError(
        "Token ou ID do grupo não configurado no .env"
    )

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

mensagem = (
    "🏠 TESTE DO RASTREADOR DE PREÇOS!\n\n"
    "✅ Grupo configurado com sucesso.\n"
    "📲 Os alertas de queda de preço serão enviados aqui."
)

try:
    resposta = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": mensagem
        },
        timeout=15
    )

    resultado = resposta.json()

    if resultado.get("ok"):
        print("✅ Mensagem enviada com sucesso!")
        print("Grupo:", CHAT_ID)
    else:
        print("❌ Erro ao enviar mensagem:")
        print(resultado)

except requests.RequestException as erro:
    print("❌ Erro de conexão:", erro)