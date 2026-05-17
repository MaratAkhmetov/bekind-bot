import json
import re

from app.services.llm import generate_text
from app.agent.prompts import INTENT_PROMPT


def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None


def analyze_intent(user_input: str):

    text = user_input.lower().strip()

    # =====================================
    # BUTTON ROUTING
    # =====================================

    if "🐾" in text or "help animals" in text:
        return {
            "intent": "animals",
            "category": "Animals",
            "action_type": "mixed",
            "needs_clarification": False,
            "intent_confidence": 1.0,
            "is_invalid": False,
            "is_unsupported": False,
            "keywords": ["cats", "dogs", "animals", "rescue"]
        }

    if "🌍" in text or "help environment" in text:
        return {
            "intent": "environment",
            "category": "Environment",
            "action_type": "mixed",
            "needs_clarification": False,
            "intent_confidence": 1.0,
            "is_invalid": False,
            "is_unsupported": False,
            "keywords": ["environment", "cleanup", "trees"]
        }

    if (
        "🤝" in text
        or "help people" in text
        or "help community" in text
    ):
        return {
            "intent": "community",
            "category": "Community",
            "action_type": "mixed",
            "needs_clarification": False,
            "intent_confidence": 1.0,
            "is_invalid": False,
            "is_unsupported": False,
            "keywords": ["community", "elderly", "homeless"]
        }

    # =====================================
    # QUICK INVALID DETECTION
    # =====================================

    if len(text) <= 2:
        return {
            "intent": "invalid",
            "category": "Unclear",
            "action_type": "info",
            "needs_clarification": True,
            "intent_confidence": 0.0,
            "is_invalid": True,
            "is_unsupported": False,
            "keywords": []
        }

    # =====================================
    # LLM
    # =====================================

    try:

        prompt = INTENT_PROMPT.format(
            user_input=user_input
        )

        response = generate_text(prompt)

        json_str = extract_json(response)

        if not json_str:
            raise ValueError("No JSON found")

        data = json.loads(json_str)

        mapping = {
            "animals": "Animals",
            "environment": "Environment",
            "community": "Community",
            "unclear": "Unclear",
        }

        category = mapping.get(
            str(data.get("category", "")).lower(),
            "Unclear"
        )

        return {
            "intent": data.get("intent", "unknown"),
            "category": category,
            "action_type": data.get("action_type", "info"),
            "needs_clarification": bool(
                data.get("needs_clarification", False)
            ),
            "intent_confidence": float(
                data.get("intent_confidence", 0.0)
            ),
            "is_invalid": bool(
                data.get("is_invalid", False)
            ),
            "is_unsupported": bool(
                data.get("is_unsupported", False)
            ),
            "keywords": data.get("keywords", ["help"])
        }

    except Exception as e:

        print("INTENT ERROR:", e)

        return {
            "intent": "fallback",
            "category": "Unclear",
            "action_type": "info",
            "needs_clarification": True,
            "intent_confidence": 0.0,
            "is_invalid": True,
            "is_unsupported": False,
            "keywords": []
        }