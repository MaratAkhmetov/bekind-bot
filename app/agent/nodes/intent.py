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
    # 1. RULE-BASED FAST PATH (ВАЖНО)
    # =====================================

    # 🐾 animals
    if any(x in text for x in ["animal", "cat", "dog", "stray", "pet"]):
        return {
            "intent": "animals",
            "category": "animals",
            "action_type": "mixed",
            "needs_clarification": False,
            "keywords": ["animals"]
        }

    # 🌍 environment
    if any(x in text for x in ["environment", "eco", "cleanup", "tree", "recycle"]):
        return {
            "intent": "environment",
            "category": "environment",
            "action_type": "mixed",
            "needs_clarification": False,
            "keywords": ["environment"]
        }

    # 🤝 community
    if any(x in text for x in ["community", "people", "homeless", "elderly"]):
        return {
            "intent": "community",
            "category": "community",
            "action_type": "mixed",
            "needs_clarification": False,
            "keywords": ["community"]
        }

    # 💰 donation detection (ВАЖНО)
    if "donate" in text or "donation" in text:
        if any(x in text for x in ["cat", "dog", "animal", "stray"]):
            return {
                "intent": "donation animals",
                "category": "animals",
                "action_type": "donation",
                "needs_clarification": False,
                "keywords": ["donation", "animals"]
            }

    # =====================================
    # 2. LLM FALLBACK
    # =====================================

    try:
        prompt = INTENT_PROMPT.format(user_input=user_input)

        response = generate_text(prompt)

        json_str = extract_json(response)

        if not json_str:
            raise ValueError("No JSON found")

        data = json.loads(json_str)

        category = data.get("category", "unclear")

        # 🔥 CRITICAL FIX: never allow "unclear" if keywords exist
        if category == "unclear":
            category = "community"

        return {
            "intent": data.get("intent", "unknown"),
            "category": category,
            "action_type": data.get("action_type", "info"),
            "needs_clarification": False,
            "keywords": data.get("keywords", [])
        }

    except Exception as e:

        print("INTENT ERROR:", e)

        # 🚨 SAFE DEFAULT (NEVER BREAK FLOW)
        return {
            "intent": "fallback",
            "category": "community",
            "action_type": "info",
            "needs_clarification": False,
            "keywords": []
        }