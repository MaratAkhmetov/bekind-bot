from app.services.llm import generate_text
from app.agent.prompts import INVALID_INPUT_PROMPT


def should_clarify(intent: dict) -> bool:

    if intent.get("is_invalid"):
        return True

    if intent.get("needs_clarification"):
        return True

    confidence = float(intent.get("intent_confidence", 0))

    if confidence < 0.55:
        return True

    return False


def ask_clarification(intent: dict, user_input: str = ""):

    if intent.get("is_invalid"):

        try:
            prompt = INVALID_INPUT_PROMPT.format(
                user_input=user_input
            )

            text = generate_text(prompt)

            if text and str(text).strip():
                return {
                    "type": "clarification",
                    "message": str(text).strip()
                }

        except Exception:
            pass

        return {
            "type": "clarification",
            "message": (
                "I didn’t quite understand that message. "
                "Try asking about animals, environment, or community support in Belgrade."
            )
        }

    category = str(intent.get("category", "")).lower()

    if category == "animals":
        return {
            "type": "clarification",
            "message": (
                "Would you like to help animals through volunteering, "
                "donations, fostering, or rescue support?"
            )
        }

    if category == "environment":
        return {
            "type": "clarification",
            "message": (
                "Are you interested in cleanups, tree planting, "
                "recycling, or environmental education?"
            )
        }

    if category == "community":
        return {
            "type": "clarification",
            "message": (
                "Would you like to support homeless people, "
                "elderly care, food aid, or local initiatives?"
            )
        }

    return {
        "type": "clarification",
        "message": (
            "What kind of help are you interested in — "
            "animals, environment, or community support?"
        )
    }