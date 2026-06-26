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


@app.get("/send-test")
def send_test_message():
    test_number = os.getenv("TEST_PHONE_NUMBER")

    if not test_number:
        return {
            "error": "TEST_PHONE_NUMBER is missing"
        }

    message = "Hello! I am Monir AI Personal Assistant. WhatsApp sending test is working."

    send_whatsapp_message(test_number, message)

    return {
        "status": "test message sent",
        "to": test_number
    }


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    print("Webhook verification request:", dict(params))

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {
        "error": "Webhook verification failed",
        "received_token": token
    }


@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("Incoming webhook data:", data)

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            print("No message found in webhook")
            return {
                "status": "no message found"
            }

        message = value["messages"][0]
        user_phone = message["from"]

        if message["type"] == "text":
            user_text = message["text"]["body"]
            print("User message:", user_text)

            ai_reply = ask_ai(user_text)
            print("AI reply:", ai_reply)

            send_whatsapp_message(user_phone, ai_reply)

        return {
            "status": "success"
        }

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
