import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from assistant import ask_ai

load_dotenv()

app = FastAPI()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")


@app.get("/")
def home():
    return {
        "status": "Monir WhatsApp AI Assistant is running"
    }


@app.get("/webhook")
def verify_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)

    return {
        "error": "Webhook verification failed"
    }


@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return {"status": "no message found"}

        message = value["messages"][0]
        user_phone = message["from"]

        if message["type"] == "text":
            user_text = message["text"]["body"]

            ai_reply = ask_ai(user_text)

            send_whatsapp_message(user_phone, ai_reply)

        return {"status": "success"}

    except Exception as e:
        print("Error:", e)
        return {
            "status": "error",
            "message": str(e)
        }


def send_whatsapp_message(to: str, message: str):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message[:4000]
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    print("WhatsApp API Response:", response.status_code, response.text)
