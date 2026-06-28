import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")


@app.get("/")
def home():
    return {
        "status": "MonirBot AI is running",
        "mode": "safe test mode"
    }


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    print("Webhook verify request:", dict(params))

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {
        "error": "verification failed",
        "received_token": token
    }


@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("Incoming webhook data:", data)

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            print("No message found")
            return {"status": "no message"}

        message = value["messages"][0]
        user_phone = message["from"]

        if message.get("type") == "text":
            user_text = message["text"]["body"]
            print("User message:", user_text)

            reply = f"✅ MonirBot AI working.\n\nআপনি লিখেছেন: {user_text}"
            send_whatsapp_message(user_phone, reply)

        else:
            send_whatsapp_message(
                user_phone,
                "✅ MonirBot AI working. এখন শুধু text message support করছে।"
            )

        return {"status": "success"}

    except Exception as e:
        print("Webhook error:", str(e))
        return {
            "status": "error",
            "message": str(e)
        }


def send_whatsapp_message(to: str, message: str):
    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"

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

    return response
