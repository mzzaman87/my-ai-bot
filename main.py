import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
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


@app.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Privacy Policy - Monir AI Assistant</title>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 850px; margin: 40px auto; line-height: 1.7;">
        <h1>Privacy Policy</h1>
        <p><strong>App Name:</strong> Monir AI Assistant</p>

        <h2>Overview</h2>
        <p>
            Monir AI Assistant is a WhatsApp-based AI personal assistant designed to help users
            with text-based questions, productivity, content writing, business support, and general assistance.
        </p>

        <h2>Information We Receive</h2>
        <p>
            This app may receive WhatsApp messages that users send to the connected WhatsApp number.
            These messages are used only to understand the user's request and generate a helpful response.
        </p>

        <h2>How We Use Information</h2>
        <p>
            User messages are processed only for providing AI-generated replies and improving the user experience.
            We do not sell, rent, or share user data with advertisers.
        </p>

        <h2>AI Processing</h2>
        <p>
            User messages may be processed by AI services in order to generate responses.
            The app is intended for general productivity and assistance purposes.
        </p>

        <h2>Data Sharing</h2>
        <p>
            We do not sell personal data. We do not share WhatsApp messages with advertisers.
        </p>

        <h2>User Control</h2>
        <p>
            Users can stop using this assistant at any time by not sending messages to the WhatsApp number.
            Users may also request data deletion by contacting us.
        </p>

        <h2>Contact</h2>
        <p>
            For privacy questions, contact us at:
            <strong>mzzaman0171@gmail.com</strong>
        </p>

        <p>Last updated: June 26, 2026</p>
    </body>
    </html>
    """


@app.get("/data-deletion", response_class=HTMLResponse)
def data_deletion():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Deletion Instructions - Monir AI Assistant</title>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 850px; margin: 40px auto; line-height: 1.7;">
        <h1>Data Deletion Instructions</h1>
        <p><strong>App Name:</strong> Monir AI Assistant</p>

        <p>
            To request deletion of your data, please contact us at:
            <strong>mzzaman0171@gmail.com</strong>
        </p>

        <p>
            Please include your WhatsApp number in your request so we can identify the related records,
            if any are stored.
        </p>

        <p>
            We will review and process valid deletion requests as soon as possible.
        </p>

        <p>Last updated: June 26, 2026</p>
    </body>
    </html>
    """


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

        else:
            send_whatsapp_message(
                user_phone,
                "Sorry, I can currently reply only to text messages."
            )

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

    return response
