import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
SHEET_WEBHOOK_URL = os.getenv("SHEET_WEBHOOK_URL")


# ================= HOME =================
@app.get("/")
def home():
    return {"status": "MonirBot AI running"}


# ================= WEBHOOK VERIFY =================
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params

    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))

    return {"error": "verification failed"}


# ================= MAIN WEBHOOK =================
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return {"status": "no message"}

        message = value["messages"][0]
        user_phone = message["from"]

        if message["type"] == "text":
            text = message["text"]["body"].lower()

            save_memory(user_phone, text)

            reply = handle_command(text)

            send_whatsapp_message(user_phone, reply)

        return {"status": "success"}

    except Exception as e:
        print("Error:", str(e))
        return {"status": "error"}


# ================= COMMAND HANDLER =================
def handle_command(text: str):
     if "caption" in text or "post" in text or "content" in text:
    return generate_ai_post(text)
    # HELP
    if "/help" in text:
        return "Commands: /services /price /social /publish"

    # SERVICES
    if "/services" in text or "service" in text:
        return "We provide SaaS, AI bot, Social media content services."

    # PRICE
    if "/price" in text or "price" in text or "cost" in text:
        return "Price depends on requirements. Send details."

    # SOCIAL CONTENT
    if "/social" in text or "caption" in text or "post" in text:
        return """
📱 Social Media Service

We create:
- Facebook posts
- Instagram captions
- LinkedIn posts
- YouTube titles
- TikTok captions

Send:
Business name + platform + topic
"""

    # AUTO PUBLISH
    if "/publish" in text or "auto publish" in text:
        return """
🚀 Auto Publish Service

We support:
Facebook, Instagram, LinkedIn, YouTube

Send details:
Page link + frequency + content type
"""

    # DEFAULT
    return "MonirBot AI working. Type /help"


# ================= MEMORY =================
def save_memory(phone, text):
    if not SHEET_WEBHOOK_URL:
        return

    try:
        requests.post(SHEET_WEBHOOK_URL, json={
            "type": "memory",
            "whatsapp": phone,
            "message": text
        })
    except:
        pass


# ================= WHATSAPP SEND =================
def send_whatsapp_message(to, message):

    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    requests.post(url, headers=headers, json=payload)
def generate_ai_post(text: str):

    text = text.lower()

    if "pharmacy" in text:
        return """
💊 Pharmacy Instagram Caption

"Your Health, Our Priority 💙
Get quality medicines at affordable prices!

📦 Fast Delivery
💊 Trusted Pharmacy
💰 Best Offers Available

👉 Order Now & Stay Healthy!"

#Hashtags
#Pharmacy #HealthCare #Medicine #StayHealthy #Wellness
"""

    if "hospital" in text:
        return """
🏥 Hospital Service Caption

"Advanced Healthcare for Everyone ❤️
Expert doctors & modern facilities.

🩺 24/7 Service
🏥 Trusted Care
💙 Your Health Matters

👉 Book Appointment Today!"

#Hashtags
#Hospital #Healthcare #Doctors #Health
"""

    return """
🤖 AI Content Generator

Please specify:
- Platform (Facebook / Instagram / LinkedIn)
- Topic
- Business type

Example:
"Instagram caption for fashion brand"
"""
