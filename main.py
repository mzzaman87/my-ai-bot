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
        "mode": "memory + social request save mode"
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

            social_data = extract_social_request(user_text)
            lead_data = extract_lead_data(user_text)

            if social_data:
                save_social_request(social_data)
                reply = (
                    "✅ ধন্যবাদ! আপনার Social Media / Auto Publish request গ্রহণ করা হয়েছে।\n\n"
                    "আমাদের team/admin আপনার সাথে যোগাযোগ করবে।"
                )

            elif lead_data:
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
/social - Social media content service
/post - Social media post writing service
/publish - Social media auto publish request

আপনি normal message দিলেও bot বুঝে reply করবে।
"""

    if (
        text_lower == "/services"
        or "service" in text_lower
        or "services" in text_lower
        or "ki ki" in text_lower
        or "gulo ki" in text_lower
        or "onskill" in text_lower
        or "সার্ভিস" in text_lower
        or "কি কি" in text_lower
        or "সেবা" in text_lower
    ):
        return """
✅ OnSkill IT Services

1. Hospital SaaS rental/service
2. Pharmacy SaaS rental/service
3. WhatsApp AI Assistant setup
4. AI Customer Support Bot
5. Social Media Content Writing
6. SEO Content Support
7. Website/WordPress Content Support
8. Social Media Auto Publishing Setup

Website:
https://www.onskillit.com/

Demo নিতে /demo লিখুন।
Price জানতে /price লিখুন।
Social media support জানতে /social লিখুন।
"""

    if (
        text_lower == "/hospital"
        or "hospital" in text_lower
        or "clinic" in text_lower
        or "হাসপাতাল" in text_lower
        or "ক্লিনিক" in text_lower
    ):
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
Price জানতে /price লিখুন।
"""

    if (
        text_lower == "/pharmacy"
        or "pharmacy" in text_lower
        or "medicine" in text_lower
        or "ফার্মেসি" in text_lower
        or "মেডিসিন" in text_lower
    ):
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
Price জানতে /price লিখুন।
"""

    if (
        text_lower == "/publish"
        or "auto publish" in text_lower
        or "autopublish" in text_lower
        or "publish" in text_lower
        or "schedule post" in text_lower
        or "post schedule" in text_lower
        or "automatic post" in text_lower
        or "অটো পাবলিশ" in text_lower
        or "পাবলিশ" in text_lower
        or "শিডিউল" in text_lower
    ):
        return """
🚀 Social Media Auto Publish Request

আমরা social media auto publish setup support করতে পারি।

Supported platforms:

✅ Facebook Page
✅ Instagram Business
✅ LinkedIn Page/Profile
✅ YouTube Community / Video Metadata Support
✅ Pinterest
✅ X/Twitter
✅ WhatsApp Channel/Status planning
✅ Website/WordPress blog publish support

Auto publish request save করতে নিচের format পাঠান:

Name:
Business Name:
Platform:
Page/Profile Link:
Product/Service:
Post Topic:
Tone:
Posting Frequency:
Content Type:
Phone:
WhatsApp:
Email:

Note:
Actual auto publish চালু করতে platform API/token/admin access লাগবে।
"""

    if (
        text_lower == "/social"
        if "caption" in text_lower or "post" in text_lower or "content" in text_lower:
         return """
       🤖 AI Content Generator

        আমরা আপনার জন্য ready post বানাতে পারি।

        Example লিখুন:
       👉 Instagram caption chai pharmacy offer er jonno
       👉 Facebook post chai hospital service er jonno

         ✔ Caption
        ✔ Hashtags
        ✔ CTA
        ✔ Engagement optimized post
           """
        or text_lower == "/post"
        or "social media" in text_lower
        or "facebook post" in text_lower
        or "instagram" in text_lower
        or "linkedin" in text_lower
        or "tiktok" in text_lower
        or "youtube" in text_lower
        or "pinterest" in text_lower
        or "twitter" in text_lower
        or "x post" in text_lower
        or "caption" in text_lower
        or "content" in text_lower
        or "post likhe" in text_lower
        or "post chai" in text_lower
        or "সোশ্যাল" in text_lower
        or "ফেসবুক" in text_lower
        or "ইনস্টাগ্রাম" in text_lower
        or "ইউটিউব" in text_lower
        or "ক্যাপশন" in text_lower
        or "পোস্ট" in text_lower
        or "কনটেন্ট" in text_lower
    ):
        return """
📱 Social Media Content Support

আমরা যেসব platform-এর content support করি:

✅ Facebook Post
✅ Instagram Caption
✅ LinkedIn Post
✅ TikTok Caption
✅ YouTube Title, Description & Tags
✅ Pinterest Pin Title & Description
✅ X/Twitter Post
✅ WhatsApp Status Content
✅ Short Video Script
✅ Product Promotional Copy
✅ Festival/Offer Post Content

Content request save করতে নিচের format পাঠান:

Name:
Business Name:
Platform:
Product/Service:
Post Topic:
Tone:
Phone:
WhatsApp:
Email:

Auto publish setup জানতে /publish লিখুন।
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
2. WhatsApp AI Assistant setup
3. Social Media Content Writing
4. Social Media Auto Publishing Setup
5. Number of platforms/users
6. Required features
7. Setup/customization
8. Monthly support

আপনার exact price জানতে নিচের format-এ details পাঠান:

Name:
Address:
Phone:
WhatsApp:
Email:

আমাদের team/admin আপনার requirement দেখে price জানাবে।
"""

    if (
        text_lower == "/demo"
        or "demo" in text_lower
        or "ডেমো" in text_lower
        or "দেখতে চাই" in text_lower
    ):
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

    if (
        text_lower == "/contact"
        or "contact" in text_lower
        or "phone" in text_lower
        or "যোগাযোগ" in text_lower
        or "কন্টাক্ট" in text_lower
    ):
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

    if (
        text_lower == "/human"
        or "human" in text_lower
        or "admin" in text_lower
        or "support" in text_lower
        or "মানুষ" in text_lower
        or "এডমিন" in text_lower
    ):
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

    if "hospital" in text_lower or "clinic" in text_lower or "হাসপাতাল" in text_lower or "ক্লিনিক" in text_lower:
        return "Hospital SaaS"

    if "pharmacy" in text_lower or "medicine" in text_lower or "ফার্মেসি" in text_lower or "মেডিসিন" in text_lower:
        return "Pharmacy SaaS"

    if "whatsapp" in text_lower or "bot" in text_lower or "ai assistant" in text_lower:
        return "WhatsApp AI Assistant"

    if "seo" in text_lower:
        return "SEO Content Support"

    if (
        "auto publish" in text_lower
        or "publish" in text_lower
        or "schedule post" in text_lower
        or "অটো পাবলিশ" in text_lower
        or "পাবলিশ" in text_lower
        or "শিডিউল" in text_lower
    ):
        return "Social Media Auto Publish"

    if (
        "social" in text_lower
        or "facebook" in text_lower
        or "instagram" in text_lower
        or "linkedin" in text_lower
        or "tiktok" in text_lower
        or "youtube" in text_lower
        or "pinterest" in text_lower
        or "twitter" in text_lower
        or "caption" in text_lower
        or "post" in text_lower
        or "content" in text_lower
        or "সোশ্যাল" in text_lower
        or "ফেসবুক" in text_lower
        or "ইনস্টাগ্রাম" in text_lower
        or "ইউটিউব" in text_lower
        or "পোস্ট" in text_lower
        or "কনটেন্ট" in text_lower
    ):
        return "Social Media Content"

    if "service" in text_lower or "সার্ভিস" in text_lower:
        return "Services Inquiry"

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


def extract_social_request(text: str):
    lines = text.splitlines()

    data = {
        "name": "",
        "business_name": "",
        "platform": "",
        "page_profile_link": "",
        "product_service": "",
        "post_topic": "",
        "tone": "",
        "posting_frequency": "",
        "content_type": "",
        "phone": "",
        "whatsapp": "",
        "email": "",
        "request_type": "Social Media Content"
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
        elif key in ["business name", "business"]:
            data["business_name"] = value
            found = True
        elif key == "platform":
            data["platform"] = value
            found = True
        elif key in ["page/profile link", "page link", "profile link", "page"]:
            data["page_profile_link"] = value
            found = True
        elif key in ["product/service", "product", "service"]:
            data["product_service"] = value
            found = True
        elif key in ["post topic", "topic"]:
            data["post_topic"] = value
            found = True
        elif key == "tone":
            data["tone"] = value
            found = True
        elif key in ["posting frequency", "frequency"]:
            data["posting_frequency"] = value
            found = True
        elif key in ["content type", "type"]:
            data["content_type"] = value
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

    text_lower = text.lower()

    if (
        "auto publish" in text_lower
        or "publish" in text_lower
        or "schedule" in text_lower
        or "অটো পাবলিশ" in text_lower
        or "পাবলিশ" in text_lower
        or "শিডিউল" in text_lower
    ):
        data["request_type"] = "Auto Publish Request"

    if found and (
        data["business_name"]
        or data["platform"]
        or data["product_service"]
        or data["post_topic"]
        or data["content_type"]
        or data["page_profile_link"]
    ):
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


def save_social_request(social_data: dict):
    if not SHEET_WEBHOOK_URL:
        print("SHEET_WEBHOOK_URL missing")
        return False

    social_data["type"] = "social_request"

    try:
        response = requests.post(SHEET_WEBHOOK_URL, json=social_data, timeout=15)
        print("Social Request Sheet Response:", response.status_code, response.text)
        return response.status_code == 200
    except Exception as e:
        print("Social request save error:", str(e))
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
