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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ================= HOME =================
@app.get("/")
def home():
    return {"status": "Gemini Bot Running 🚀"}


# ================= WEBHOOK VERIFY =================
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

            text = msg["text"]["body"]

            reply = ask_ai(text)

            if not reply:
                reply = "🤖 AI temporarily unavailable"

            send_whatsapp(user, reply)

        return {"status": "ok"}

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return {"status": "error"}


# ================= GEMINI AI ONLY =================
def ask_ai(prompt: str):

    try:
        if GEMINI_API_KEY:

            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

            payload = {
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ]
            }

            r = requests.post(url, json=payload, timeout=10)
            data = r.json()

            print("GEMINI DEBUG:", data)

            if "candidates" in data:
                cand = data["candidates"]
                if len(cand) > 0:
                    parts = cand[0].get("content", {}).get("parts", [])
                    if len(parts) > 0:
                        return parts[0].get("text")

    except Exception as e:
        print("Gemini error:", e)

    return None


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
    except Exception as e:
        print("WhatsApp error:", e)
