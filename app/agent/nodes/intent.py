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
    # BUTTON ROUTING (FAST PATH)
    # =====================================

    if "🐾" in text or "help animals" in text:
        return {
            "intent": "animals",
            "category": "Animals",
            "action_type": "mixed",
            "needs_clarification": False,
            "keywords": ["cats", "dogs", "stray", "animals", "rescue"]
        }

    if "🌍" in text or "help environment" in text:
        return {
            "intent": "environment",
            "category": "Environment",
            "action_type": "mixed",
            "needs_clarification": False,
            "keywords": ["environment", "cleanup", "trees", "ecology"]
        }

    if "🤝" in text or "community" in text:
        return {
            "intent": "community",
            "category": "Community",
            "action_type": "mixed",
            "needs_clarification": False,
            "keywords": ["community", "homeless", "elderly", "refugees"]
        }

    # =====================================
    # DONATION FIRST (ВАЖНО)
    # =====================================

    if "donate" in text or "donation" in text:

        # animals donation
        if any(x in text for x in [
            "cat", "dog", "animal", "stray", "pet"
        ]):
            return {
                "intent": "donation_animals",
                "category": "Animals",
                "action_type": "donation",
                "needs_clarification": False,
                "keywords": ["cats", "dogs", "animal rescue"]
            }

        # general donation
        return {
            "intent": "donation_community",
            "category": "Community",
            "action_type": "donation",
            "needs_clarification": False,
            "keywords": ["charity", "help", "community"]
        }

    # =====================================
    # RULE-BASED SEARCH
    # =====================================

    if any(x in text for x in [
        "cat", "dog", "animal", "stray", "pet"
    ]):
        return {
            "intent": "animals",
            "category": "Animals",
            "action_type": "mixed",
            "needs_clarification": False,
            "keywords": ["animals"]
        }

    if any(x in text for x in [
        "eco", "environment", "tree",
        "cleanup", "recycle", "ecology"
    ]):
        return {
            "intent": "environment",
            "category": "Environment",
            "action_type": "mixed",
            "needs_clarification": False,
            "keywords": ["environment"]
        }

    if any(x in text for x in [
        "community", "people", "help",
        "homeless", "elderly", "charity"
    ]):
        return {
            "intent": "community",
            "category": "Community",
            "action_type": "mixed",
            "needs_clarification": False,
            "keywords": ["community"]
        }

    # =====================================
    # LLM FALLBACK
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

        category = data.get("category")

        # normalize category
        mapping = {
            "animals": "Animals",
            "environment": "Environment",
            "community": "Community"
        }

        category = mapping.get(
            str(category).lower(),
            "Community"
        )

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
            "category": "Community",
            "action_type": "info",
            "needs_clarification": False,
            "keywords": ["help"]
        }