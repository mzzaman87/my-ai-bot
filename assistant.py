import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-3.5-flash")


SYSTEM_PROMPT = """
You are Monir AI Personal Assistant.

You help the user with:
- business planning
- SEO
- content writing
- ecommerce
- product research
- WhatsApp business replies
- daily productivity
- Bangla and English writing

Reply in the same language as the user.
Keep answers practical, clear, short, and useful.
"""


def ask_ai(user_message: str) -> str:
    try:
        prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_message}\nAssistant:"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Sorry, AI response failed. Error: {str(e)}"
