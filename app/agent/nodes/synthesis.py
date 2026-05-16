import json

from app.agent.prompts import ADVISORY_SYNTHESIS_PROMPT
from app.services.llm import generate_text

MAX_ITEMS = 3


def _build_intro(user_input: str) -> str:
    text = user_input.lower()

    if "animal" in text or "🐾" in text:
        return "Here are some ways you can help animals in Belgrade:"
    if "environment" in text or "🌍" in text:
        return "If you’d like to support the environment in Belgrade, here are a few real initiatives:"
    if "community" in text or "people" in text or "help people" in text:
        return "Here are meaningful ways to help people in your community:"

    return "Here are real ways you can make a positive impact:"


def _inject_links(text: str, items: list, user_input: str) -> str:
    """
    STRICT POSITIONAL LINK INJECTION (stable version + intro protection)
    """

    FOOTER = "💚 Small actions create real impact."
    text = text.replace(FOOTER, "").strip()

    lines = text.split("\n")

    result_blocks = []
    current = []

    for line in lines:
        if line.strip().startswith(("1.", "2.", "3.")):
            if current:
                result_blocks.append("\n".join(current).strip())
                current = []
        current.append(line)

    if current:
        result_blocks.append("\n".join(current).strip())

    org_blocks = []
    for b in result_blocks:
        if any(b.strip().startswith(f"{i}.") for i in range(1, 10)):
            org_blocks.append(b)

    org_blocks = org_blocks[:3]

    while len(org_blocks) < 3:
        org_blocks.append("")

    final = []

    for i, item in enumerate(items[:MAX_ITEMS]):
        block = org_blocks[i] if i < len(org_blocks) else ""

        website = item.get("website")
        instagram = item.get("instagram")
        facebook = item.get("facebook")

        links = []

        if website:
            links.append(website)

        if instagram:
            links.append(instagram)
        elif facebook:
            links.append(facebook)

        if links:
            block += "\n\n" + "\n".join(links)

        final.append(block.strip())

    result = "\n\n\n".join(final).strip()

    # 🔥 CRITICAL FIX: ensure intro ALWAYS exists
    first_line = result.split("\n", 1)[0].strip() if result else ""

    if first_line.startswith(("1.", "2.", "3.")):
        intro = _build_intro(user_input)
        result = intro + "\n\n" + result

    return result + "\n\n" + FOOTER


def synthesize_answer(user_input, local_data, web_data):
    data = local_data if local_data else web_data if web_data else []

    if not data:
        return "No initiatives found."

    items = data[:MAX_ITEMS]

    while len(items) < MAX_ITEMS:
        items.append({})

    text = _build_intro(user_input) + "\n\n"

    for i, item in enumerate(items, start=1):
        name = item.get("name", "Unknown")
        description = item.get("description", "")

        text += f"{i}. {name}\n"
        text += f"{description}\n\n"

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

    while len(items) < MAX_ITEMS:
        items.append({})

    organizations_json = _items_payload(items)

    prompt = ADVISORY_SYNTHESIS_PROMPT.format(
        user_input=user_input,
        n=len(items),
        organizations_json=organizations_json,
    )

    try:
        out = generate_text(prompt)

        if not out or not str(out).strip():
            raise ValueError("empty llm")

        out_s = str(out).strip()

        if "I'm having trouble processing this right now" in out_s:
            raise ValueError("llm soft fail")

        return _inject_links(out_s, items, user_input)

    except Exception:
        return synthesize_answer(user_input, local_data, web_data)