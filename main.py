import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from assistant import ask_ai

load_dotenv()

app = FastAPI()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
SHEET_WEBHOOK_URL = os.getenv("SHEET_WEBHOOK_URL")


# ================= BUSINESS CONTEXT =================
BUSINESS_CONTEXT = """
Business Name: OnSkill IT / MonirBot AI
Website: https://www.onskillit.com/

Services:
- Hospital SaaS
- Pharmacy SaaS
- WhatsApp AI Assistant
- Customer Support Bot
- Content Writing
- SEO Services
"""


# ================= HOME =================
@app.get("/")
def home():
    return {"status": "MonirBot AI Running"}


# ================= WHATSAPP VERIFY =================
@app.get("/webhook")
async def verify(request: Request):
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

        message = value["messages"][0]
        user_phone = message["from"]
        user_text = message["text"]["body"].strip()

        # 1. SAVE MEMORY
        save_memory({
            "whatsapp": user_phone,
            "last_query": user_text
        })

        # 2. CHECK LEAD FORMAT
        lead = extract_lead(user_text)
        if lead:
            save_lead(lead)
            send_whatsapp(user_phone, "ধন্যবাদ! আপনার তথ্য গ্রহণ করা হয়েছে। আমরা যোগাযোগ করবো।")
            return {"status": "lead saved"}

        # 3. NORMAL AI REPLY
        reply = ask_ai(f"{BUSINESS_CONTEXT}\nUser: {user_text}")
        send_whatsapp(user_phone, reply)

        return {"status": "success"}

    except Exception as e:
        print("Error:", e)
        return {"status": "error"}


# ================= SEND MESSAGE =================
def send_whatsapp(to, message):
    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"

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

    requests.post(url, headers=headers, json=payload)


# ================= LEAD SAVE =================
def extract_lead(text):
    lines = text.split("\n")
    data = {}

    for line in lines:
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip().lower()] = v.strip()

    if "name" in data or "phone" in data:
        return data

    return None


def save_lead(data):
    if SHEET_WEBHOOK_URL:
        requests.post(SHEET_WEBHOOK_URL, json=data)


# ================= MEMORY =================
def save_memory(data):
    if SHEET_WEBHOOK_URL:
        try:
            requests.post(SHEET_WEBHOOK_URL, json={
                "type": "memory",
                "data": data
            })
        except:
            pass


# ================= SIMPLE COMMAND HELP =================
def help_text():
    return """
/help
/services
/hospital
/pharmacy
/demo
"""
