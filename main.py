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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ================= HOME =================
@app.get("/")
def home():
    return {"status": "MonirBot AI Running 🚀"}


# ================= WEBHOOK VERIFY =================
@app.get("/webhook")
def verify(request: Request):

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {"status": "failed"}


# ================= MAIN WEBHOOK =================
@app.post("/webhook")
async def webhook(request: Request):

    data = await request.json()

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return {"status": "no message"}

        msg = value["messages"][0]
        user = msg["from"]

        if msg["type"] == "text":
            text = msg["text"]["body"].lower()

            save_memory(user, text)

            reply = handle_command(text)

            send_whatsapp(user, reply)

        return {"status": "ok"}

    except Exception as e:
        print("ERROR:", e)
        return {"status": "error"}


# ================= COMMAND SYSTEM =================
def handle_command(text: str):

    # 🔥 AI FIRST (SMART BRAIN)
    ai = ask_ai(text)
    if ai:
        return ai

    # HELP
    if "/help" in text:
        return "Commands: /services /price /social /publish"

    # SERVICES
    if "/services" in text or "service" in text:
        return "We provide SaaS, AI Bot, Social Media & Automation services."

    # PRICE
    if "/price" in text or "price" in text or "cost" in text:
        return "Price depends on requirements. Send details."

    # SOCIAL
    if "/social" in text or "caption" in text or "post" in text:
        return social_reply(text)

    # PUBLISH
    if "/publish" in text or "auto publish" in text:
        return publish_reply()

    return "MonirBot AI working 🤖 Type /help"


# ================= AI FUNCTION =================
def ask_ai(prompt: str):

    if not GEMINI_API_KEY:
        return None

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        data = res.json()

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except:
        return None


# ================= SOCIAL REPLY =================
def social_reply(text: str):

    if "pharmacy" in text:
        return """💊 Pharmacy Post:
Stay healthy with trusted medicine.

#pharmacy #health #medicine"""

    if "hospital" in text:
        return """🏥 Hospital Post:
Best healthcare services for everyone.

#hospital #health #care"""

    return "Send: Instagram caption + topic (e.g. pharmacy offer)"


# ================= PUBLISH =================
def publish_reply():
    return """
🚀 Auto Publish System

Send:
- Platform
- Page link
- Content type
- Frequency
"""


# ================= MEMORY =================
def save_memory(phone, text):

    if not SHEET_WEBHOOK_URL:
        return

    try:
        requests.post(SHEET_WEBHOOK_URL, json={
            "type": "memory",
            "whatsapp": phone,
            "message": text
        }, timeout=5)
    except:
        pass


# ================= WHATSAPP SEND =================
def send_whatsapp(to, message):

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

    try:
        requests.post(url, headers=headers, json=payload, timeout=10)
    except:
        pass
