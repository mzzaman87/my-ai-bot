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
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ================= HOME =================
@app.get("/")
def home():
    return {"status": "MonirBot AI Running 🚀"}


# ================= DASHBOARD =================
@app.get("/dashboard")
def dashboard():
    return {
        "status": "ACTIVE",
        "bot": "MonirBot AI SaaS",
        "ai": "Claude + Gemini Hybrid"
    }


# ================= WEBHOOK VERIFY =================
@app.get("/webhook")
def verify(request: Request):

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {"status": "failed"}


# ================= WEBHOOK MAIN =================
@app.post("/webhook")
async def webhook(request: Request):

    try:
        data = await request.json()

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


# ================= AI ENGINE (FINAL STABLE) =================
def ask_ai(prompt: str):

    system_prompt = "You are a helpful SaaS assistant. Reply short and clear."

    # ---------- CLAUDE ----------
    try:
        if CLAUDE_API_KEY:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 300,
                    "messages": [
                        {
                            "role": "user",
                            "content": system_prompt + "\nUser: " + prompt
                        }
                    ]
                },
                timeout=10
            )

            data = r.json()

            if isinstance(data, dict):
                content = data.get("content")
                if isinstance(content, list) and len(content) > 0:
                    text = content[0].get("text")
                    if text:
                        return text

    except Exception as e:
        print("Claude error:", e)

    # ---------- GEMINI ----------
    try:
        if GEMINI_API_KEY:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
                json={
                    "contents": [
                        {"parts": [{"text": system_prompt + "\nUser: " + prompt}]}
                    ]
                },
                timeout=10
            )

            data = r.json()

            if "candidates" in data:
                cand = data["candidates"]
                if len(cand) > 0:
                    parts = cand[0].get("content", {}).get("parts", [])
                    if len(parts) > 0:
                        return parts[0].get("text")

    except Exception as e:
        print("Gemini error:", e)

    # ---------- FINAL FALLBACK ----------
    return "🤖 AI temporarily unavailable"


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
