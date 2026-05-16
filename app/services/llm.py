import google.generativeai as genai
from app.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

# ✅ stable model
model = genai.GenerativeModel("gemini-1.5-flash")


def generate_text(prompt: str) -> str:
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.8,
                "top_p": 0.9,
                "max_output_tokens": 700,
            }
        )
        return response.text
    except Exception as e:
        return "I'm having trouble processing this right now. Try again."