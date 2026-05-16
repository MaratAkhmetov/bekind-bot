import os
import logging
from mistralai import Mistral

from app.config import MISTRAL_API_KEY

logger = logging.getLogger(__name__)

# =========================
# Init Mistral client
# =========================
client = Mistral(api_key=MISTRAL_API_KEY)

MODEL_NAME = "mistral-small-latest"


def generate_text(prompt: str) -> str:
    """
    Generates text using Mistral model for synthesis layer.
    """

    try:
        logger.info(f"[LLM] Using model: {MODEL_NAME}")

        response = client.chat.complete(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,
            top_p=0.9,
            max_tokens=700,
        )

        text = response.choices[0].message.content

        logger.info("[LLM] Response generated successfully")

        print("\n========== LLM RESPONSE ==========")
        print(text)
        print("==================================\n")

        return text.strip()

    except Exception as e:

        logger.error(f"[LLM ERROR] {str(e)}")

        print("\n========== LLM ERROR ==========")
        print(str(e))
        print("================================\n")

        return "I'm having trouble processing this right now. Try again."