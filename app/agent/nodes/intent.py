import json
import re
from app.services.llm import generate_text
from app.agent.prompts import INTENT_PROMPT


def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None


def analyze_intent(user_input: str):
    prompt = INTENT_PROMPT.format(user_input=user_input)
    response = generate_text(prompt)

    try:
        json_str = extract_json(response)

        if not json_str:
            raise ValueError("No JSON found")

        data = json.loads(json_str)

        return {
            "intent": data.get("intent", "unknown"),
            "category": data.get("category", "unclear"),
            "action_type": data.get("action_type", "info"),
            "needs_clarification": bool(data.get("needs_clarification", False)),
            "keywords": data.get("keywords", [])
        }

    except Exception:
        # ⚠️ SAFE FALLBACK (NO LOOP!)
        return {
            "intent": "unknown",
            "category": "unclear",
            "action_type": "info",
            "needs_clarification": False,
            "keywords": []
        }