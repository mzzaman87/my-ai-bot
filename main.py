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


@app.get("/")
def home():
    return {
        "status": "MonirBot AI is running"
    }


@app.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Privacy Policy - MonirBot AI</title>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 850px; margin: 40px auto; line-height: 1.7;">
        <h1>Privacy Policy</h1>
        <p><strong>App Name:</strong> MonirBot AI</p>

        <h2>Overview</h2>
        <p>
            MonirBot AI is a WhatsApp-based AI personal assistant designed to help users
            with text-based questions, productivity, content writing, business support,
            ecommerce, SEO, and general assistance.
        </p>

        <h2>Information We Receive</h2>
        <p>
            This app may receive WhatsApp messages that users send to the connected WhatsApp number.
            These messages are used only to understand the user's request and generate a helpful response.
        </p>

        <h2>How We Use Information</h2>
        <p>
            User messages are processed only for providing AI-generated replies.
            We do not sell, rent, or share user data with advertisers.
        </p>

        <h2>AI Processing</h2>
        <p>
            User messages may be processed by AI services in order to generate responses.
        </p>

        <h2>Data Sharing</h2>
        <p>
            We do not sell personal data. We do not share WhatsApp messages with advertisers.
        </p>

        <h2>User Control</h2>
        <p>
            Users can stop using this assistant at any time by not sending messages to the WhatsApp number.
        </p>

        <h2>Contact</h2>
        <p>
            For privacy questions, contact us at:
            <strong>mzzaman0171@gmail.com</strong>
        </p>

        <p>Last updated: June 26, 2026</p>
    </body>
    </html>
    """


@app.get("/data-deletion", response_class=HTMLResponse)
def data_deletion():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Deletion Instructions - MonirBot AI</title>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 850px; margin: 40px auto; line-height: 1.7;">
        <h1>Data Deletion Instructions</h1>
        <p><strong>App Name:</strong> MonirBot AI</p>

        <p>
            To request deletion of your data, please contact us at:
            <strong>mzzaman0171@gmail.com</strong>
        </p>

        <p>
            Please include your WhatsApp number in your request so we can identify the related records,
            if any are stored.
        </p>

        <p>
            We will review and process valid deletion requests as soon as possible.
        </p>

        <p>Last updated: June 26, 2026</p>
    </body>
    </html>
    """


@app.get("/send-test")
def send_test_message():
    test_number = os.getenv("TEST_PHONE_NUMBER")

    if not test_number:
        return {
            "error": "TEST_PHONE_NUMBER is missing"
        }

    message = "Hello! I am MonirBot AI. WhatsApp sending test is working."

    send_whatsapp_message(test_number, message)

    return {
        "status": "test message sent",
        "to": test_number
    }


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    print("Webhook verification request:", dict(params))

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {
        "error": "Webhook verification failed",
        "received_token": token
    }


@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("Incoming webhook data:", data)

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            print("No message found in webhook")
            return {
                "status": "no message found"
            }

        message = value["messages"][0]
        user_phone = message["from"]

        if message["type"] == "text":
            user_text = message["text"]["body"].strip()
            print("User message:", user_text)

            reply_text = handle_command(user_text)
            print("Bot reply:", reply_text)

            send_whatsapp_message(user_phone, reply_text)

        else:
            send_whatsapp_message(
                user_phone,
                "Sorry, I can currently reply only to text messages."
            )

        return {
            "status": "success"
        }

    except Exception as e:
        print("Webhook error:", str(e))
        return {
            "status": "error",
            "message": str(e)
        }


def handle_command(user_text: str) -> str:
    lower_text = user_text.lower()

    if lower_text == "/help":
        return get_help_message()

    if lower_text == "/about":
        return (
            "I am MonirBot AI, your WhatsApp-based business and productivity assistant.\n\n"
            "I can help you write social media posts, captions, ads, SEO content, product descriptions, "
            "customer replies, business plans, translations, and daily task plans.\n\n"
            "Type /help to see all commands."
        )

    if lower_text.startswith("/post"):
        content = remove_command(user_text, "/post")
        if not content:
            return "Please write your topic after /post.\n\nExample:\n/post Premium A2 Ghee offer for Facebook and Instagram"
        prompt = f"""
Create a complete social media post for this topic:

{content}

Include:
1. Attractive caption
2. Short headline
3. CTA
4. Hashtags
5. Facebook version
6. Instagram version
7. LinkedIn version
8. Pinterest title and description
9. Twitter/X short version

Reply in the user's language.
"""
        return ask_ai(prompt)

    if lower_text.startswith("/caption"):
        content = remove_command(user_text, "/caption")
        if not content:
            return "Please write your topic after /caption.\n\nExample:\n/caption Eid offer for ladies abaya"
        prompt = f"""
Write an attractive social media caption for:

{content}

Include:
1. Hook
2. Main caption
3. CTA
4. 10 relevant hashtags

Reply in the user's language.
"""
        return ask_ai(prompt)

    if lower_text.startswith("/hashtags"):
        content = remove_command(user_text, "/hashtags")
        if not content:
            return "Please write your topic after /hashtags.\n\nExample:\n/hashtags abaya business in Kolkata"
        prompt = f"""
Generate relevant hashtags for this topic:

{content}

Give:
1. 10 popular hashtags
2. 10 niche hashtags
3. 5 local hashtags if relevant

Reply in the user's language.
"""
        return ask_ai(prompt)

    if lower_text.startswith("/customer"):
        content = remove_command(user_text, "/customer")
        if not content:
            return "Please paste the customer message after /customer.\n\nExample:\n/customer দাম কত?"
        prompt = f"""
Write a polite, professional WhatsApp customer reply for this message:

{content}

Make it friendly, clear, and sales-focused.
Reply in the user's language.
"""
        return ask_ai(prompt)

    if lower_text.startswith("/seo"):
        content = remove_command(user_text, "/seo")
        if not content:
            return "Please write your topic/product/service after /seo.\n\nExample:\n/seo local SEO service for optometry clinic"
        prompt = f"""
Create SEO content for:

{content}

Include:
1. SEO title
2. Meta description
3. Main keywords
4. Long-tail keywords
5. FAQ ideas
6. Short SEO paragraph

Reply in the user's language.
"""
        return ask_ai(prompt)

    if lower_text.startswith("/product"):
        content = remove_command(user_text, "/product")
        if not content:
            return "Please write product details after /product.\n\nExample:\n/product A2 Ghee 10 lb tin price $222"
        prompt = f"""
Create ecommerce product content for:

{content}

Include:
1. Product title
2. Short description
3. Long description
4. Key benefits
5. Feature bullets
6. CTA
7. Marketplace-friendly version

Reply in the user's language.
"""
        return ask_ai(prompt)

    if lower_text.startswith("/idea"):
        content = remove_command(user_text, "/idea")
        if not content:
            return "Please write your topic after /idea.\n\nExample:\n/idea Facebook content ideas for software tools business"
        prompt = f"""
Give practical ideas for:

{content}

Include:
1. 10 ideas
2. Best 3 recommendations
3. How to start
4. Quick action plan

Reply in the user's language.
"""
        return ask_ai(prompt)

    if lower_text.startswith("/plan"):
        content = remove_command(user_text, "/plan")
        if not content:
            return "Please write what plan you need after /plan.\n\nExample:\n/plan 7 day content plan for ecommerce business"
        prompt = f"""
Create a clear step-by-step plan for:

{content}

Include:
1. Goal
2. Step-by-step plan
3. Daily actions
4. Tools needed
5. Final checklist

Reply in the user's language.
"""
        return ask_ai(prompt)

    if lower_text.startswith("/translate"):
        content = remove_command(user_text, "/translate")
        if not content:
            return "Please write text after /translate.\n\nExample:\n/translate আমার ব্যবসার জন্য একটি পোস্ট লিখুন"
        prompt = f"""
Translate this text naturally. If it is Bangla, translate to English. If it is English, translate to Bangla.

Text:
{content}

Also make it clean and professional.
"""
        return ask_ai(prompt)

    if lower_text.startswith("/ad"):
        content = remove_command(user_text, "/ad")
        if not content:
            return "Please write product/offer details after /ad.\n\nExample:\n/ad Canva Pro access 99 taka per month"
        prompt = f"""
Create high-converting ad copy for:

{content}

Include:
1. Primary text
2. Headline
3. Description
4. CTA
5. 3 alternative hooks
6. Urgency line
7. WhatsApp sales message version

Reply in the user's language.
"""
        return ask_ai(prompt)

    return ask_ai(user_text)


def remove_command(text: str, command: str) -> str:
    return text[len(command):].strip()


def get_help_message() -> str:
    return """
🤖 MonirBot AI Commands

Use these commands in WhatsApp:

1️⃣ /help
Show all commands.

2️⃣ /post [topic]
Create social media post for Facebook, Instagram, LinkedIn, Pinterest, Twitter/X.

Example:
/post Premium A2 Ghee offer, 10 lb tin, only $222

3️⃣ /caption [topic]
Create attractive caption with CTA and hashtags.

Example:
/caption Eid offer for abaya collection

4️⃣ /hashtags [topic]
Generate hashtags.

Example:
/hashtags ecommerce software tools business

5️⃣ /customer [customer message]
Create polite customer reply.

Example:
/customer দাম কত?

6️⃣ /seo [topic]
Create SEO title, meta description, keywords, FAQ ideas.

Example:
/seo optometry clinic local SEO service

7️⃣ /product [product details]
Create product title, description, benefits, CTA.

Example:
/product A2 Ghee 10 lb tin price $222

8️⃣ /idea [topic]
Generate business/content/marketing ideas.

Example:
/idea Facebook post ideas for software tools

9️⃣ /plan [goal]
Create step-by-step plan.

Example:
/plan 7 day marketing plan for my business

🔟 /translate [text]
Translate Bangla to English or English to Bangla.

Example:
/translate আমি আপনার অর্ডার কনফার্ম করছি

1️⃣1️⃣ /ad [product/offer]
Create ad copy for Facebook/Instagram/WhatsApp.

Example:
/ad Canva Pro access 99 taka monthly offer

1️⃣2️⃣ /about
About MonirBot AI.

You can also ask anything normally without command.
"""


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
