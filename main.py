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


BUSINESS_CONTEXT = """
Business Name: OnSkill IT / MonirBot AI

Website:
https://www.onskillit.com/

Main Business Services:
1. Hospital SaaS rental/service
2. Pharmacy SaaS rental/service
3. WhatsApp AI Assistant setup
4. AI Customer Support Bot
5. Social Media Content Writing
6. Facebook, Instagram, LinkedIn, Pinterest, Twitter/X Caption Writing
7. Ecommerce Product Title and Description Writing
8. SEO Title, Meta Description, Keyword and FAQ Writing
9. Facebook/Instagram Ad Copy Writing
10. Business Planning and Daily Task Planning
11. Bangla-English Translation
12. Website/WordPress Content Support
13. Future Upgrade: Auto publish to Facebook, Instagram, LinkedIn, Pinterest, Website, Tumblr, Reddit, and Twitter/X

Hospital SaaS Service:
We provide Hospital SaaS on rental/service basis. It can help hospitals and clinics manage patient records, appointments, doctors, billing, prescriptions, reports, daily hospital operations, and staff workflow.

Pharmacy SaaS Service:
We provide Pharmacy SaaS on rental/service basis. It can help pharmacies manage medicine stock, sales, purchase, expiry tracking, billing, customer records, supplier records, reports, and daily pharmacy operations.

Customer Support Style:
- Reply politely and professionally.
- If user asks about Hospital SaaS or Pharmacy SaaS, explain the benefits clearly.
- If user asks price, say pricing depends on requirement, number of users, features, setup, customization, and support level.
- Ask for business name, phone number, service needed, and location.
- If user asks for demo, ask them to share name, phone number, business type, and preferred demo time.
- If user asks about website, share: https://www.onskillit.com/

Important:
If user asks about pricing, reply that pricing depends on service, platform, and automation level.
If user asks to talk to human/admin, ask them to share their name, phone number, business name, service needed, and message.
If user asks about social media publishing, explain that content creation is available now and auto-publishing can be connected platform by platform using APIs.
"""


@app.get("/")
def home():
    return {
        "status": "MonirBot AI is running",
        "business": "OnSkill IT",
        "website": "https://www.onskillit.com/"
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
        <p><strong>Business:</strong> OnSkill IT</p>
        <p><strong>Website:</strong> https://www.onskillit.com/</p>

        <h2>Overview</h2>
        <p>
            MonirBot AI is a WhatsApp-based AI assistant designed to help users with
            customer support, business inquiries, SaaS service information, content writing,
            ecommerce support, SEO, productivity, and general assistance.
        </p>

        <h2>Information We Receive</h2>
        <p>
            This app may receive WhatsApp messages that users send to the connected WhatsApp number.
            These messages are used only to understand the user's request and generate a helpful response.
        </p>

        <h2>How We Use Information</h2>
        <p>
            User messages are processed only for providing AI-generated replies and customer support.
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
        <p><strong>Business:</strong> OnSkill IT</p>

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

    message = "Hello! I am MonirBot AI from OnSkill IT. WhatsApp sending test is working."

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
        return get_about_message()

    if lower_text == "/services":
        return get_services_message()

    if lower_text == "/hospital":
        return get_hospital_saas_message()

    if lower_text == "/pharmacy":
        return get_pharmacy_saas_message()

    if lower_text == "/support":
        return get_support_message()

    if lower_text == "/faq":
        return get_faq_message()

    if lower_text == "/price":
        return get_price_message()

    if lower_text == "/demo":
        return get_demo_message()

    if lower_text == "/contact":
        return get_contact_message()

    if lower_text == "/policy":
        return get_policy_message()

    if lower_text == "/human":
        return get_human_support_message()

    if lower_text.startswith("/post"):
        content = remove_command(user_text, "/post")
        if not content:
            return "Please write your topic after /post.\n\nExample:\n/post Hospital SaaS demo offer for clinics"
        prompt = f"""
{BUSINESS_CONTEXT}

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
            return "Please write your topic after /caption.\n\nExample:\n/caption Hospital SaaS for clinic management"
        prompt = f"""
{BUSINESS_CONTEXT}

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
            return "Please write your topic after /hashtags.\n\nExample:\n/hashtags pharmacy software Bangladesh"
        prompt = f"""
{BUSINESS_CONTEXT}

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
            return "Please paste the customer message after /customer.\n\nExample:\n/customer Hospital software price কত?"
        prompt = f"""
{BUSINESS_CONTEXT}

Write a polite, professional WhatsApp customer reply for this message:

{content}

Make it friendly, clear, helpful, and sales-focused.
If needed, ask one follow-up question.
Reply in the user's language.
"""
        return ask_ai(prompt)

    if lower_text.startswith("/support-reply"):
        content = remove_command(user_text, "/support-reply")
        if not content:
            return "Please paste the customer issue after /support-reply.\n\nExample:\n/support-reply Pharmacy software login হচ্ছে না"
        prompt = f"""
{BUSINESS_CONTEXT}

Write a customer support reply for this issue:

{content}

Include:
1. A polite greeting
2. Acknowledgement of the issue
3. Simple solution steps
4. Ask for screenshot/details if needed
5. Friendly closing

Reply in the user's language.
"""
        return ask_ai(prompt)

    if lower_text.startswith("/seo"):
        content = remove_command(user_text, "/seo")
        if not content:
            return "Please write your topic/product/service after /seo.\n\nExample:\n/seo Hospital SaaS Bangladesh"
        prompt = f"""
{BUSINESS_CONTEXT}

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
            return "Please write product/service details after /product.\n\nExample:\n/product Pharmacy SaaS monthly rental service"
        prompt = f"""
{BUSINESS_CONTEXT}

Create product/service content for:

{content}

Include:
1. Product/service title
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
            return "Please write your topic after /idea.\n\nExample:\n/idea Facebook content ideas for Hospital SaaS"
        prompt = f"""
{BUSINESS_CONTEXT}

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
            return "Please write what plan you need after /plan.\n\nExample:\n/plan 7 day marketing plan for Pharmacy SaaS"
        prompt = f"""
{BUSINESS_CONTEXT}

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
            return "Please write text after /translate.\n\nExample:\n/translate Hospital software demo available"
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
            return "Please write product/offer details after /ad.\n\nExample:\n/ad Hospital SaaS monthly rental service for clinics"
        prompt = f"""
{BUSINESS_CONTEXT}

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

    support_keywords = [
        "service", "services", "support", "price", "pricing", "contact",
        "hospital", "pharmacy", "saas", "demo", "software", "website",
        "সার্ভিস", "সেবা", "দাম", "প্রাইস", "মূল্য", "যোগাযোগ", "সাপোর্ট",
        "হাসপাতাল", "ফার্মেসি", "সফটওয়্যার", "সফটওয়্যার", "ডেমো",
        "কি কি করেন", "কী কী করেন", "আপনারা কি করেন", "ওয়েবসাইট", "ওয়েবসাইট"
    ]

    if any(keyword in lower_text for keyword in support_keywords):
        prompt = f"""
{BUSINESS_CONTEXT}

User asked:
{user_text}

Answer as MonirBot AI customer support for OnSkill IT.
Explain our services clearly.
If the user asks about Hospital SaaS, explain Hospital SaaS benefits.
If the user asks about Pharmacy SaaS, explain Pharmacy SaaS benefits.
If the question is about price, say pricing depends on requirement and ask for details.
If the user asks for demo, ask for name, phone number, business type, and preferred demo time.
Keep the reply helpful, polite, and business-friendly.
Reply in the user's language.
"""
        return ask_ai(prompt)

    prompt = f"""
{BUSINESS_CONTEXT}

User message:
{user_text}

Reply as MonirBot AI for OnSkill IT.
If the user asks about our services, explain from the business context.
If it is a normal request, answer normally.
Reply in the user's language.
"""
    return ask_ai(prompt)


def remove_command(text: str, command: str) -> str:
    return text[len(command):].strip()


def get_help_message() -> str:
    return """
🤖 MonirBot AI Commands

General:
1️⃣ /help
Show all commands.

2️⃣ /about
About MonirBot AI and OnSkill IT.

3️⃣ /services
Know our services.

4️⃣ /hospital
Hospital SaaS service details.

5️⃣ /pharmacy
Pharmacy SaaS service details.

6️⃣ /support
Customer support information.

7️⃣ /faq
Frequently asked questions.

8️⃣ /price
Pricing information.

9️⃣ /demo
Request demo information.

🔟 /contact
Contact information.

1️⃣1️⃣ /policy
Service policy.

1️⃣2️⃣ /human
Request human/admin support.

Content & Marketing:
1️⃣3️⃣ /post [topic]
Create social media post for Facebook, Instagram, LinkedIn, Pinterest, Twitter/X.

1️⃣4️⃣ /caption [topic]
Create attractive caption with CTA and hashtags.

1️⃣5️⃣ /hashtags [topic]
Generate hashtags.

1️⃣6️⃣ /ad [product/offer]
Create ad copy for Facebook/Instagram/WhatsApp.

Customer Support:
1️⃣7️⃣ /customer [customer message]
Create polite customer reply.

1️⃣8️⃣ /support-reply [issue]
Create support reply for customer issue.

SEO & Service Content:
1️⃣9️⃣ /seo [topic]
Create SEO title, meta description, keywords, FAQ ideas.

2️⃣0️⃣ /product [product/service details]
Create product/service title, description, benefits, CTA.

Planning:
2️⃣1️⃣ /idea [topic]
Generate business/content/marketing ideas.

2️⃣2️⃣ /plan [goal]
Create step-by-step plan.

Translation:
2️⃣3️⃣ /translate [text]
Translate Bangla to English or English to Bangla.

You can also ask anything normally without command.

Website:
https://www.onskillit.com/
"""


def get_about_message() -> str:
    return """
🤖 About MonirBot AI

MonirBot AI is a WhatsApp-based AI business and customer support assistant for OnSkill IT.

OnSkill IT provides:
✅ Hospital SaaS rental/service
✅ Pharmacy SaaS rental/service
✅ WhatsApp AI Assistant setup
✅ AI customer support bot
✅ Content, SEO, and digital support

Website:
https://www.onskillit.com/

Type /services to know more.
"""


def get_services_message() -> str:
    return """
✅ Our Services — OnSkill IT / MonirBot AI

1. Hospital SaaS Rental/Service
Manage patient records, appointments, doctors, billing, prescriptions, reports, and daily hospital operations.

2. Pharmacy SaaS Rental/Service
Manage medicine stock, sales, purchase, expiry tracking, billing, customer records, and pharmacy reports.

3. WhatsApp AI Assistant Setup
AI bot setup for WhatsApp-based support and business automation.

4. AI Customer Support Bot
Automated customer reply system for common questions and support.

5. Social Media Content Writing
Facebook, Instagram, LinkedIn, Pinterest, Twitter/X post and caption writing.

6. SEO Content Support
SEO title, meta description, keyword ideas, blog outline, and service page content.

7. Website/WordPress Content Support
Website copy, blog content, product/service content.

8. Future Upgrade
Auto social media publishing using platform API connection.

Website:
https://www.onskillit.com/
"""


def get_hospital_saas_message() -> str:
    return """
🏥 Hospital SaaS Service

OnSkill IT provides Hospital SaaS on rental/service basis.

It can help hospitals and clinics manage:
✅ Patient records
✅ Appointments
✅ Doctor management
✅ Billing
✅ Prescriptions
✅ Reports
✅ Daily hospital operations
✅ Staff workflow

Best for:
- Clinics
- Diagnostic centers
- Small hospitals
- Healthcare service providers

For demo, type:
/demo
"""


def get_pharmacy_saas_message() -> str:
    return """
💊 Pharmacy SaaS Service

OnSkill IT provides Pharmacy SaaS on rental/service basis.

It can help pharmacies manage:
✅ Medicine stock
✅ Sales
✅ Purchase
✅ Expiry tracking
✅ Billing
✅ Customer records
✅ Supplier records
✅ Daily reports

Best for:
- Pharmacy shops
- Medicine stores
- Healthcare product sellers
- Small and medium pharmacy businesses

For demo, type:
/demo
"""


def get_support_message() -> str:
    return """
🛟 Customer Support

How can we help you?

You can ask about:
- Hospital SaaS
- Pharmacy SaaS
- Demo request
- Pricing
- WhatsApp AI assistant
- AI customer support bot
- Social media content
- SEO content
- Website/WordPress support

For human support, type:
/human
"""


def get_faq_message() -> str:
    return """
❓ FAQ — OnSkill IT / MonirBot AI

Q1: OnSkill IT কী service দেয়?
A: Hospital SaaS, Pharmacy SaaS, WhatsApp AI Assistant, customer support bot, content, SEO, and website support.

Q2: Hospital SaaS কী?
A: Hospital/clinic management software service, যা patient, appointment, billing, doctor, prescription, report manage করতে help করে।

Q3: Pharmacy SaaS কী?
A: Pharmacy management software service, যা stock, sales, purchase, expiry, billing, customer record manage করতে help করে।

Q4: Pricing কত?
A: Pricing requirement, features, users, setup and support level অনুযায়ী হবে।

Q5: Demo পাওয়া যাবে?
A: হ্যাঁ, demo request করতে /demo লিখুন।

Q6: PC বন্ধ থাকলেও bot কাজ করবে?
A: হ্যাঁ, কারণ backend cloud hosting-এ চলে।

Q7: Website কী?
A: https://www.onskillit.com/
"""


def get_price_message() -> str:
    return """
💰 Pricing Information

Pricing depends on your requirement.

Cost may depend on:
1. Hospital SaaS or Pharmacy SaaS
2. Number of users
3. Required features
4. Setup/customization level
5. Monthly support
6. Training/support requirement
7. Extra automation or AI integration

Please share:
Name:
Phone:
Business Type:
Service Needed:
Number of Users:
Location:

Then we can suggest the best package.
"""


def get_demo_message() -> str:
    return """
📅 Demo Request

Sure, we can arrange a demo.

Please send your details:

Name:
Phone:
Business Name:
Business Type: Hospital / Clinic / Pharmacy / Other
Service Needed: Hospital SaaS / Pharmacy SaaS / AI Assistant
Preferred Demo Time:
Location:

Our admin/team will review and contact you.
"""


def get_contact_message() -> str:
    return """
📞 Contact / Support

Website:
https://www.onskillit.com/

For support, please send:

Name:
Phone:
Business Name:
Service Needed:
Message:

You can also type:
/human

Our team/admin will review your request.
"""


def get_policy_message() -> str:
    return """
📌 Service Policy

1. We provide SaaS rental/service, AI assistant, content, customer support and automation setup services.
2. Pricing depends on requirements, users, features and support level.
3. AI replies depend on user input and connected tools.
4. Social media auto-publishing requires platform API/token permission.
5. Some platforms may require approval, paid API, or business verification.
6. We do not sell user data.
7. Users can stop using the assistant anytime.
"""


def get_human_support_message() -> str:
    return """
👤 Human Support Request

Please send your details in this format:

Name:
Phone:
Business Name:
Business Type:
Service Needed:
Location:
Message:

Our admin/team will review your request.
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
