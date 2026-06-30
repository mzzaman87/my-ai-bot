import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

# ================= ENV =================
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ================= HOME =================
@app.get("/")
def home():
    return {"status": "Gemini WhatsApp Bot Running 🚀"}


# ================= WEBHOOK VERIFY =================
@app.get("/webhook")
def verify(request: Request):

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {"status": "error"}


# ================= WEBHOOK =================
@app.post("/webhook")
async def webhook(request: Request):

    try:
        data = await request.json()

        entry = data["entry"][0]["changes"][0]["value"]

        if "messages" not in entry:
            return {"status": "no message"}

        msg = entry["messages"][0]
        user = msg["from"]

        if msg["type"] == "text":

            user_text = msg["text"]["body"]

            reply = ask_ai(user_text)

            if not reply:
                reply = "🤖 AI temporarily unavailable"

            send_whatsapp(user, reply)

        return {"status": "ok"}

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return {"status": "error"}


# ================= GEMINI AI (CLEAN + SAFE) =================
def ask_ai(prompt: str):

    try:
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

        r = requests.post(url, json=payload, timeout=10)
        data = r.json()

        print("GEMINI RESPONSE:", data)

        # SAFE CHECK
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"]

        # ERROR LOG
        if "error" in data:
            print("GEMINI ERROR:", data["error"])

    except Exception as e:
        print("Gemini Exception:", e)

    return None


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
        "text": {
            "body": message[:4000]
        }
    }

    try:
        requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        print("WhatsApp Error:", e)
