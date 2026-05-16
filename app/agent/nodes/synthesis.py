import json

from app.agent.prompts import ADVISORY_SYNTHESIS_PROMPT
from app.services.llm import generate_text

MAX_ITEMS = 3


def _inject_links(text: str, items: list) -> str:
    """
    STRICT POSITIONAL LINK INJECTION (stable version)
    """

    FOOTER = "💚 Small actions create real impact."

    text = text.replace(FOOTER, "").strip()

    lines = text.split("\n")

    result_blocks = []
    current = []

    for line in lines:
        # detect start of org block
        if line.strip().startswith(("1.", "2.", "3.")):
            if current:
                result_blocks.append("\n".join(current).strip())
                current = []
        current.append(line)

    if current:
        result_blocks.append("\n".join(current).strip())

    # keep ONLY real org blocks (skip intro garbage)
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

    return "\n\n\n".join(final).strip() + "\n\n" + FOOTER


def synthesize_answer(user_input, local_data, web_data):

    data = local_data if local_data else web_data if web_data else []

    if not data:
        return "No initiatives found."

    items = data[:MAX_ITEMS]

    # HARD FIX: ensure always 3
    while len(items) < MAX_ITEMS:
        items.append({})

    text = "Here are real initiatives you can support:\n\n"

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

    # HARD GUARANTEE: always 3 items
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

        return _inject_links(out_s, items)

    except Exception:
        return synthesize_answer(user_input, local_data, web_data)