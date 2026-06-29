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
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")


# ================= HOME =================
@app.get("/")
def home():
    return {"status": "MonirBot AI SaaS LIVE 🚀"}


# ================= ADMIN =================
@app.get("/admin")
def admin():
    return {
        "status": "Admin Panel Active",
        "system": "MonirBot SaaS AI",
        "modules": ["AI", "Memory", "Lead", "Social", "Automation"]
    }


# ================= VERIFY =================
@app.get("/webhook")
def verify(request: Request):

    if request.query_params.get("hub.mode") == "subscribe" and request.query_params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(request.query_params.get("hub.challenge"))

    return {"status": "failed"}


# ================= WEBHOOK =================
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

            intent = detect_intent(text)

            save_memory(user, text, intent)

            if is_lead(text):
                save_lead(user, text)

            reply = ask_ai(text)

            if not reply:
                reply = fallback(text)

            send_whatsapp(user, reply)

        return {"status": "ok"}

    except Exception as e:
        print("ERROR:", e)
        return {"status": "error"}


# ================= CLAUDE AI =================
def ask_ai(prompt: str):

    if not CLAUDE_API_KEY:
        return None

    url = "https://api.anthropic.com/v1/messages"

    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    system_prompt = """
You are MonirBot AI SaaS Assistant.

You help with:
- Hospital SaaS
- Pharmacy SaaS
- Business automation
- Social media content
- Pricing & sales

Reply short, clear, professional.
"""

    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 500,
        "messages": [
            {
                "role": "user",
                "content": system_prompt + "\nUser: " + prompt
            }
        ]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        data = res.json()
        return data["content"][0]["text"]
    except:
        return None


# ================= INTENT =================
def detect_intent(text: str):

    if "price" in text or "cost" in text or "koto" in text:
        return "pricing"

    if "hospital" in text:
        return "hospital"

    if "pharmacy" in text:
        return "pharmacy"

    if "social" in text or "caption" in text:
        return "marketing"

    if "demo" in text:
        return "lead"

    return "general"


# ================= LEAD =================
def is_lead(text: str):

    keywords = ["price", "demo", "buy", "cost", "contact", "offer"]

    return any(k in text for k in keywords)


def save_lead(phone, text):

    if not SHEET_WEBHOOK_URL:
        return

    try:
        requests.post(SHEET_WEBHOOK_URL, json={
            "type": "lead",
            "whatsapp": phone,
            "message": text
        })
    except:
        pass


# ================= MEMORY =================
def save_memory(phone, text, intent):

    if not SHEET_WEBHOOK_URL:
        return

    try:
        requests.post(SHEET_WEBHOOK_URL, json={
            "type": "memory",
            "whatsapp": phone,
            "message": text,
            "intent": intent
        })
    except:
        pass


# ================= FALLBACK =================
def fallback(text: str):

    if "hospital" in text:
        return "🏥 Hospital SaaS available. Contact for demo."

    if "pharmacy" in text:
        return "💊 Pharmacy SaaS available. Contact for details."

    if "price" in text:
        return "💰 Price depends on requirements. Send details."

    if "social" in text:
        return "📱 Social media content service available."

    if "demo" in text:
        return "📅 Send details for demo request."

    return "🤖 MonirBot AI working. Type /help"


# ================= WHATSAPP =================
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
        "text": {"body": message[:4000]}
    }

    try:
        requests.post(url, headers=headers, json=payload, timeout=10)
    except:
        pass
