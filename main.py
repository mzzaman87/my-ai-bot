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


@app.get("/")
def home():
    return {
        "status": "MonirBot AI is running",
        "mode": "memory read + natural price intent mode"
    }


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {"error": "verification failed"}


@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("Incoming webhook data:", data)

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return {"status": "no message"}

        message = value["messages"][0]
        user_phone = message["from"]

        if message.get("type") == "text":
            user_text = message["text"]["body"].strip()

            previous_memory = get_memory(user_phone)

            current_interest = detect_service_interest(user_text)

            save_memory(
                whatsapp=user_phone,
                last_message=user_text,
                last_query=user_text,
                service_interest=current_interest
            )

            lead_data = extract_lead_data(user_text)

            if lead_data:
                save_lead_to_sheet(lead_data)
                reply = (
                    "✅ ধন্যবাদ! আপনার তথ্য গ্রহণ করা হয়েছে।\n\n"
                    "আমাদের team/admin আপনার সাথে যোগাযোগ করবে।"
                )
            else:
                reply = handle_command(user_text, previous_memory)

            send_whatsapp_message(user_phone, reply)

        else:
            send_whatsapp_message(
                user_phone,
                "✅ MonirBot AI working. এখন শুধু text message support করছে।"
            )

        return {"status": "success"}

    except Exception as e:
        print("Webhook error:", str(e))
        return {"status": "error", "message": str(e)}


def handle_command(text: str, previous_memory=None) -> str:
    text_lower = text.lower().strip()

    if text_lower == "/help":
        return """
🤖 MonirBot AI Commands

/help - সব command দেখুন
/services - আমাদের services দেখুন
/hospital - Hospital SaaS details
/pharmacy - Pharmacy SaaS details
/price - Pricing information
/demo - Demo request format
/contact - Contact information
/human - Human support request

আপনি normal message দিলেও bot reply করবে।
"""

    if text_lower == "/services":
        return """
✅ OnSkill IT Services

1. Hospital SaaS rental/service
2. Pharmacy SaaS rental/service
3. WhatsApp AI Assistant setup
4. AI Customer Support Bot
5. Social Media Content Writing
6. SEO Content Support
7. Website/WordPress Content Support

Website:
https://www.onskillit.com/
"""

    if text_lower == "/hospital":
        return """
🏥 Hospital SaaS Service

আমাদের Hospital SaaS hospital/clinic management সহজ করতে সাহায্য করে।

Features:
✅ Patient records
✅ Appointment management
✅ Doctor management
✅ Billing
✅ Prescription
✅ Reports
✅ Daily hospital operations

Demo নিতে /demo লিখুন।
"""

    if text_lower == "/pharmacy":
        return """
💊 Pharmacy SaaS Service

আমাদের Pharmacy SaaS pharmacy business manage করতে সাহায্য করে।

Features:
✅ Medicine stock
✅ Sales
✅ Purchase
✅ Expiry tracking
✅ Billing
✅ Customer records
✅ Supplier records
✅ Reports

Demo নিতে /demo লিখুন।
"""

    if (
        text_lower == "/price"
        or "price" in text_lower
        or "pricing" in text_lower
        or "cost" in text_lower
        or "charge" in text_lower
        or "dam" in text_lower
        or "koto" in text_lower
        or "koto taka" in text_lower
        or "কত" in text_lower
        or "দাম" in text_lower
        or "মূল্য" in text_lower
        or "খরচ" in text_lower
    ):
        return """
💰 Pricing Information

Pricing depend করে:

1. Hospital SaaS না Pharmacy SaaS
2. Number of users
3. Required features
4. Setup/customization
5. Monthly support

আপনার exact price জানতে নিচের format-এ details পাঠান:

Name:
Address:
Phone:
WhatsApp:
Email:

আমাদের team/admin আপনার requirement দেখে price জানাবে।
"""

    if text_lower == "/demo":
        return """
📅 Demo Request

Demo request করার জন্য নিচের format-এ তথ্য পাঠান:

Name:
Address:
Phone:
WhatsApp:
Email:

আপনার তথ্য পেলে আমাদের team/admin যোগাযোগ করবে।
"""

    if text_lower == "/contact":
        return """
📞 Contact

Website:
https://www.onskillit.com/

Support request করতে নিচের format পাঠান:

Name:
Address:
Phone:
WhatsApp:
Email:
"""

    if text_lower == "/human":
        return """
👤 Human Support Request

Please send your details:

Name:
Address:
Phone:
WhatsApp:
Email:

আমাদের admin/team আপনার সাথে যোগাযোগ করবে।
"""

    memory_line = ""

    if previous_memory:
        old_interest = previous_memory.get("service_interest", "")
        if old_interest and old_interest != "General Inquiry":
            memory_line = (
                f"\n\n🧠 আমি দেখছি আপনি আগে {old_interest} নিয়ে জানতে চেয়েছিলেন।"
                "\nআপনি চাইলে demo/price details জানতে পারেন।"
            )

    return (
        "✅ MonirBot AI working.\n\n"
        f"আপনি লিখেছেন: {text}"
        f"{memory_line}\n\n"
        "Command দেখতে /help লিখুন।"
    )


def detect_service_interest(text: str) -> str:
    text_lower = text.lower()

    if "hospital" in text_lower or "clinic" in text_lower or "হাসপাতাল" in text_lower:
        return "Hospital SaaS"

    if "pharmacy" in text_lower or "medicine" in text_lower or "ফার্মেসি" in text_lower:
        return "Pharmacy SaaS"

    if "whatsapp" in text_lower or "bot" in text_lower or "ai assistant" in text_lower:
        return "WhatsApp AI Assistant"

    if "seo" in text_lower:
        return "SEO Content Support"

    if "social" in text_lower or "facebook" in text_lower or "post" in text_lower:
        return "Social Media Content"

    return "General Inquiry"


def extract_lead_data(text: str):
    lines = text.splitlines()

    data = {
        "name": "",
        "address": "",
        "phone": "",
        "whatsapp": "",
        "email": ""
    }

    found = False

    for line in lines:
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        if key == "name":
            data["name"] = value
            found = True
        elif key == "address":
            data["address"] = value
            found = True
        elif key == "phone":
            data["phone"] = value
            found = True
        elif key in ["whatsapp", "whatsapps", "wa"]:
            data["whatsapp"] = value
            found = True
        elif key == "email":
            data["email"] = value
            found = True

    if found and (data["name"] or data["phone"] or data["whatsapp"] or data["email"]):
        return data

    return None


def get_memory(whatsapp: str):
    if not SHEET_WEBHOOK_URL:
        print("SHEET_WEBHOOK_URL missing")
        return None

    try:
        response = requests.get(
            SHEET_WEBHOOK_URL,
            params={"whatsapp": whatsapp},
            timeout=15
        )

        print("Memory Read Response:", response.status_code, response.text)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "found":
                return data.get("memory")

        return None

    except Exception as e:
        print("Memory read error:", str(e))
        return None


def save_lead_to_sheet(lead_data: dict):
    if not SHEET_WEBHOOK_URL:
        print("SHEET_WEBHOOK_URL missing")
        return False

    try:
        response = requests.post(SHEET_WEBHOOK_URL, json=lead_data, timeout=15)
        print("Lead Sheet Response:", response.status_code, response.text)
        return response.status_code == 200
    except Exception as e:
        print("Lead save error:", str(e))
        return False


def save_memory(whatsapp: str, last_message: str, last_query: str, service_interest: str):
    if not SHEET_WEBHOOK_URL:
        print("SHEET_WEBHOOK_URL missing")
        return False

    memory_data = {
        "type": "memory",
        "name": "",
        "whatsapp": whatsapp,
        "last_message": last_message,
        "last_query": last_query,
        "service_interest": service_interest
    }

    try:
        response = requests.post(SHEET_WEBHOOK_URL, json=memory_data, timeout=15)
        print("Memory Sheet Response:", response.status_code, response.text)
        return response.status_code == 200
    except Exception as e:
        print("Memory save error:", str(e))
        return False


def send_whatsapp_message(to: str, message: str):
    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"

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

    response = requests.post(url, headers=headers, json=payload)

    print("WhatsApp API Response:", response.status_code, response.text)

    return response
