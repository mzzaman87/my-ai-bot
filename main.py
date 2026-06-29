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


# ================= VERIFY =================
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params

    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))

    return {"error": "verification failed"}


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


# ================= COMMANDS =================
def handle_command(text: str):

    if "/help" in text:
        return "Commands: /services /price /social /publish"

    if "/services" in text or "service" in text:
        return "We provide SaaS, AI Bot, Social Media services."

    if "/price" in text or "price" in text:
        return "Price depends on requirements. Send details."

    if "/social" in text or "caption" in text or "post" in text:
        return social_reply(text)

    if "/publish" in text or "auto publish" in text:
        return publish_reply()

    return "MonirBot AI working. Type /help"


# ================= SOCIAL =================
def social_reply(text: str):

    if "pharmacy" in text:
        return "💊 Pharmacy post: Stay healthy with trusted medicine. #health #pharmacy"

    if "hospital" in text:
        return "🏥 Hospital post: Best healthcare for everyone. #hospital #health"

    return "Send: Instagram caption + topic (e.g. pharmacy offer)"


# ================= PUBLISH =================
def publish_reply():
    return """
🚀 Auto Publish System

Send details:
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
        })
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

    requests.post(url, headers=headers, json=payload)
