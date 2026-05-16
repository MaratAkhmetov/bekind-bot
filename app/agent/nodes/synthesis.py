import json

from app.agent.prompts import ADVISORY_SYNTHESIS_PROMPT
from app.services.llm import generate_text

MAX_ITEMS = 3


def synthesize_answer(user_input, local_data, web_data):

    data = local_data if local_data else web_data if web_data else []

    if not data:
        return "No initiatives found."

    text = "Here are real initiatives you can support:\n\n"

    for i, item in enumerate(data[:MAX_ITEMS], start=1):

        name = item.get("name", "Unknown")
        description = item.get("description", "")

        website = item.get("website")
        instagram = item.get("instagram")
        facebook = item.get("facebook")

        text += f"{i}. {name}\n"
        text += f"{description}\n"

        # 🔥 FIXED RULE: deterministic priority
        if website:
            text += f"🌐 Website: {website}\n"

        if instagram:
            text += f"📸 Instagram: {instagram}\n"
        elif facebook:
            text += f"📘 Facebook: {facebook}\n"

        text += "\n"

    text += "💚 Small actions create real impact."

    return text


def _items_payload(items):
    rows = []
    for it in items[:MAX_ITEMS]:
        rows.append(
            {
                "name": it.get("name") or "Unknown",
                "description": (it.get("description") or "").strip(),
                "tags": (it.get("tags") or "").strip(),
                "help_types": (it.get("help_types") or "").strip(),
                "practical_help": (it.get("practical_help") or "").strip(),
                "website": (it.get("website") or "").strip(),
                "instagram": (it.get("instagram") or "").strip(),
                "facebook": (it.get("facebook") or "").strip(),
            }
        )
    return json.dumps(rows, ensure_ascii=False, indent=2)


def synthesize_advisory(user_input, local_data, web_data):

    data = local_data if local_data else web_data if web_data else []

    if not data:
        return "No initiatives found."

    items = list(data[:MAX_ITEMS])
    organizations_json = _items_payload(items)
    n = len(items)

    prompt = ADVISORY_SYNTHESIS_PROMPT.format(
        user_input=user_input,
        n=n,
        organizations_json=organizations_json,
    )

    try:
        out = generate_text(prompt)

        if not out or not str(out).strip():
            raise ValueError("empty llm")

        out_s = str(out).strip()

        if "I'm having trouble processing this right now" in out_s:
            raise ValueError("llm api soft fail")

        return out_s

    except Exception:
        return synthesize_answer(user_input, local_data, web_data)