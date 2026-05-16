import google.generativeai as genai
from app.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

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

        print("\n========== GEMINI RESPONSE ==========")
        print(response.text)
        print("=====================================\n")

        return response.text

    except Exception as e:

        print("\n========== GEMINI ERROR ==========")
        print(str(e))
        print("==================================\n")

        return "I'm having trouble processing this right now. Try again."