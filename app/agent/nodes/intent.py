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
            "is_relevant": True,
            "relevance_confidence": 1.0,
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
            "is_relevant": True,
            "relevance_confidence": 1.0,
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
            "is_relevant": True,
            "relevance_confidence": 1.0,
            "keywords": ["community", "elderly", "homeless"]
        }

    # =====================================
    # DIRECT DETECTION (SAFE MODE KEPT)
    # =====================================

    STRICT_MODE = True

    animal_words = [
        "animal",
        "animals",
        "cat",
        "cats",
        "dog",
        "dogs",
        "stray",
        "shelter",
        "rescue",
    ]

    community_words = [
        "homeless",
        "elderly",
        "food bank",
        "community",
        "people",
        "refugees",
        "donate money",
    ]

    random_patterns = [
        "suggest a good deed",
        "random good deed",
        "give me ideas",
        "show me options",
        "something meaningful",
        "suggest something kind",
        "random volunteering",
        "предложи случайные",
        "случайное доброе дело",
    ]

    # =====================================
    # RANDOM GOOD DEED
    # =====================================

    if any(p in text for p in random_patterns):
        return {
            "intent": "random_good_deed",
            "category": "random_good_deed",
            "action_type": "mixed",
            "needs_clarification": False,
            "intent_confidence": 1.0,
            "is_invalid": False,
            "is_relevant": True,
            "relevance_confidence": 1.0,
            "keywords": ["volunteering", "community", "animals"]
        }

    # =====================================
    # QUICK INVALID DETECTION
    # =====================================

    if len(text) <= 2:
        return {
            "intent": "invalid",
            "category": "Unclear",
            "action_type": "info",
            "needs_clarification": False,
            "intent_confidence": 0.0,
            "is_invalid": True,
            "is_relevant": False,
            "relevance_confidence": 0.0,
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
            "random_good_deed": "random_good_deed",
        }

        category = mapping.get(
            str(data.get("category", "")).lower(),
            "Unclear"
        )

        return {
            "intent": data.get("intent", "unknown"),
            "category": category,
            "action_type": data.get("action_type", "info"),
            "needs_clarification": bool(data.get("needs_clarification", False)),
            "intent_confidence": float(data.get("intent_confidence", 0.0)),
            "is_invalid": bool(data.get("is_invalid", False)),
            "is_relevant": bool(data.get("is_relevant", True)),
            "relevance_confidence": float(data.get("relevance_confidence", 0.5)),
            "keywords": data.get("keywords", ["help"])
        }

    except Exception as e:

        print("INTENT ERROR:", e)

        return {
            "intent": "fallback",
            "category": "Unclear",
            "action_type": "info",
            "needs_clarification": False,
            "intent_confidence": 0.0,
            "is_invalid": False,
            "is_relevant": True,
            "relevance_confidence": 0.0,
            "keywords": []
        }