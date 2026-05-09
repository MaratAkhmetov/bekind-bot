import json
import re
from app.services.llm import generate_text
from app.agent.prompts import INTENT_PROMPT


def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None


def analyze_intent(user_input: str):

    text = user_input.lower()

    # =====================================
    # 1. RULE-BASED FAST PATH (ОБЯЗАТЕЛЬНО)
    # =====================================

    if any(x in text for x in ["cat", "dog", "animal", "stray", "pet"]):
        return {
            "intent": "animals",
            "category": "animals",
            "action_type": "mixed",
            "needs_clarification": False,
            "keywords": ["animals"]
        }

    if any(x in text for x in ["eco", "environment", "tree", "cleanup", "recycle"]):
        return {
            "intent": "environment",
            "category": "environment",
            "action_type": "mixed",
            "needs_clarification": False,
            "keywords": ["environment"]
        }

    if any(x in text for x in ["community", "people", "help", "homeless", "elderly"]):
        return {
            "intent": "community",
            "category": "community",
            "action_type": "mixed",
            "needs_clarification": False,
            "keywords": ["community"]
        }

    if "donate" in text or "donation" in text:
        if any(x in text for x in ["cat", "dog", "animal", "stray"]):
            return {
                "intent": "donation_animals",
                "category": "animals",
                "action_type": "donation",
                "needs_clarification": False,
                "keywords": ["donation", "animals"]
            }

    # =====================================
    # 2. LLM fallback
    # =====================================

    try:
        prompt = INTENT_PROMPT.format(user_input=user_input)
        response = generate_text(prompt)

        json_str = extract_json(response)
        if not json_str:
            raise ValueError("No JSON found")

        data = json.loads(json_str)

        category = data.get("category", "community")

        # ❗ NEVER UNCLEAR in production flow
        if category == "unclear" or not category:
            category = "community"

        return {
            "intent": data.get("intent", "unknown"),
            "category": category,
            "action_type": data.get("action_type", "info"),
            "needs_clarification": False,
            "keywords": data.get("keywords", ["help"])
        }

    except Exception as e:
        print("INTENT ERROR:", e)

        return {
            "intent": "fallback",
            "category": "community",
            "action_type": "info",
            "needs_clarification": False,
            "keywords": ["help"]
        }