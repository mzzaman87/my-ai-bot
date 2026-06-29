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
    return {
        "status": "MonirBot SaaS CORE LIVE 🚀",
        "modules": ["AI", "CRM", "Memory", "Leads", "Social", "Admin"]
    }


# ================= ADMIN DASHBOARD API =================
@app.get("/admin")
def admin():
    return {
        "status": "Admin Panel Ready",
        "features": {
            "leads": "active",
            "memory": "active",
            "ai": "active",
            "social": "active"
        }
    }


# ================= WEBHOOK VERIFY =================
@app.get("/webhook")
def verify(request: Request):

    if request.query_params.get("hub.mode") == "subscribe" and request.query_params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(request.query_params.get("hub.challenge"))

    return {"status": "failed"}


# ================= MAIN BOT ENGINE =================
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

            reply = ai_engine(text)

            send_whatsapp(user, reply)

        return {"status": "ok"}

    except Exception as e:
        print("ERROR:", e)
        return {"status": "error"}


# ================= AI ENGINE =================
def ai_engine(prompt: str):

    system_prompt = """
You are MonirBot AI SaaS Assistant.

You help users with:
- Hospital SaaS
- Pharmacy SaaS
- Social Media Content
- Business Automation
- Marketing & Sales

Reply:
- Short
- Smart
- Business focused
"""

    # Try Gemini AI
    if GEMINI_API_KEY:
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": system_prompt + "\nUser: " + prompt}
                    ]
                }
            ]
        }

        try:
            res = requests.post(url, json=payload, timeout=10)
            data = res.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except:
            pass

    return fallback(prompt)


# ================= INTENT DETECTION =================
def detect_intent(text: str):

    if "price" in text or "cost" in text or "koto" in text:
        return "pricing"

    if "hospital" in text:
        return "hospital"

    if "pharmacy" in text:
        return "pharmacy"

    if "social" in text or "caption" in text or "post" in text:
        return "marketing"

    if "demo" in text:
        return "lead"

    return "general"


# ================= LEAD SYSTEM =================
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


# ================= MEMORY SYSTEM =================
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


# ================= FALLBACK AI =================
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
        return "📅 Send details for demo booking."

    return "🤖 MonirBot AI working. Type /help"


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
        "text": {"body": message[:4000]}
    }

    try:
        requests.post(url, headers=headers, json=payload, timeout=10)
    except:
        pass
