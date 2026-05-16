import logging
from mistralai.client import MistralClient

from app.config import MISTRAL_API_KEY

logger = logging.getLogger(__name__)

client = MistralClient(api_key=MISTRAL_API_KEY)

MODEL_NAME = "mistral-small-latest"


def generate_text(prompt: str) -> str:
    try:
        logger.info(f"[LLM] Using model: {MODEL_NAME}")

        response = client.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            top_p=0.9,
            max_tokens=700,
        )

        text = response.choices[0].message.content

        return text.strip()

    except Exception as e:
        logger.error(f"[LLM ERROR] {str(e)}")
        return "I'm having trouble processing this right now. Try again."