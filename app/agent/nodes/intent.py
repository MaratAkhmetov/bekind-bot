import json
from app.services.llm import generate_text
from app.agent.prompts import INTENT_PROMPT


def analyze_intent(user_input: str):
    prompt = INTENT_PROMPT.format(user_input=user_input)
    response = generate_text(prompt)

    try:
        data = json.loads(response)

        return {
            "intent": data.get("intent", "unknown"),
            "category": data.get("category", "unclear"),
            "action_type": data.get("action_type", "info"),
            "needs_clarification": data.get("needs_clarification", False),
            "keywords": data.get("keywords", [])
        }

    except Exception:
        return {
            "intent": "unknown",
            "category": "unclear",
            "action_type": "info",
            "needs_clarification": True,
            "keywords": []
        }