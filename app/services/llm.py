import google.generativeai as genai
from app.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

# ✅ stable model
model = genai.GenerativeModel("gemini-1.0-pro")


def generate_text(prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "I'm having trouble processing this right now. Try again."