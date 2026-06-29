import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# ================= ENV =================
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
SHEET_WEBHOOK_URL = os.getenv("SHEET_WEBHOOK_URL")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ================= HOME =================
@app.get("/")
def home():
    return {"status": "MonirBot AI SaaS LIVE 🚀"}


# ================= DASHBOARD =================
@app.get("/dashboard")
def dashboard():
    return {
        "status": "ACTIVE",
        "bot": "MonirBot AI SaaS",
        "ai": "Claude + Gemini Hybrid",
        "features": ["Lead", "Memory", "WhatsApp", "AI Reply"]
    }


# ================= WEBHOOK VERIFY =================
@app.get("/webhook")
def verify(request: Request):

    if request.query_params.get("hub.mode") == "subscribe" and request.query_params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(request.query_params.get("hub.challenge"))

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

            text = msg["text"]["body"]

            # AI reply
            reply = ask_ai(text)

            if not reply:
                reply = "🤖 AI temporarily unavailable. Try again later."

            # Lead + Memory save
            save_memory(user, text)

            if is_lead(text):
                save_lead(user, text)

            send_whatsapp(user, reply)

        return {"status": "ok"}

    except Exception as e:
        print("ERROR:", e)
        return {"status": "error"}


# ================= AI ENGINE (STABLE HYBRID) =================
def ask_ai(prompt: str):

    system_prompt = "You are a smart SaaS AI assistant. Reply short and helpful."

    # ---------- CLAUDE ----------
    try:
        if CLAUDE_API_KEY:
            url = "https://api.anthropic.com/v1/messages"

            headers = {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": system_prompt + "\nUser: " + prompt
                    }
                ]
            }

            r = requests.post(url, headers=headers, json=payload, timeout=10)

            if r.status_code == 200:
                data = r.json()
                if "content" in data:
                    return data["content"][0]["text"]

    except Exception as e:
        print("Claude error:", e)

    # ---------- GEMINI ----------
    try:
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

            r = requests.post(url, json=payload, timeout=10)

            if r.status_code == 200:
                data = r.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        print("Gemini error:", e)

    return None


# ================= LEAD =================
def is_lead(text: str):
    keywords = ["price", "demo", "buy", "cost", "contact", "offer"]
    return any(k in text.lower() for k in keywords)


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
