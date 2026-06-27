from fastapi import FastAPI, Request
import requests

app = FastAPI()

# ================= CONFIG =================
VERIFY_TOKEN = "monirbot_verify"

WHATSAPP_TOKEN = "YOUR_WHATSAPP_TOKEN"
PHONE_NUMBER_ID = "YOUR_PHONE_NUMBER_ID"

# ================= HOME =================
@app.get("/")
def home():
    return {"status": "MonirBot AI running"}

# ================= WEBHOOK VERIFY =================
@app.get("/webhook")
def verify(hub_mode: str = None, hub_verify_token: str = None, hub_challenge: str = None):

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)

    return "Invalid verify token"

# ================= RECEIVE MESSAGE =================
@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]

        user_number = message["from"]
        user_text = message["text"]["body"]

        reply = f"আপনি লিখেছেন: {user_text}"

        send_whatsapp_message(user_number, reply)

        return {"status": "sent"}

    except Exception as e:
        print("Error:", e)
        return {"status": "error"}

# ================= SEND MESSAGE =================
def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

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
