import json
import re

from app.agent.prompts import (
    ADVISORY_SYNTHESIS_PROMPT,
    INTRO_PROMPT,
)

from app.services.llm import generate_text
from app.agent.memory import build_context_text

MAX_ITEMS = 3


def _is_noise_input(text: str) -> bool:
    if not text:
        return True

    t = text.strip().lower()

    if len(t) < 3:
        return True

    letters = sum(c.isalpha() for c in t)
    if len(t) > 0 and letters / len(t) < 0.3:
        return True

    if re.fullmatch(r"(.)\1{4,}", t):
        return True

    return False


def _build_intro(user_input: str) -> str:
    try:
        prompt = INTRO_PROMPT.format(user_input=user_input)
        out = generate_text(prompt)

        if out and str(out).strip():
            intro = str(out).strip()

            intro = intro.replace("\n", " ").strip()
            intro = intro.strip('"').strip("'").strip()

            intro = re.sub(r"\s+", " ", intro).strip()
            intro = re.sub(r"[\"'*_#]", "", intro)

            if not intro.endswith((".", "!", "?")):
                intro += "."

            return intro

    except Exception:
        pass

    return "Here are real ways you can make a positive impact."


def _format_links(item: dict, seen_urls: set) -> str:
    website = (item.get("website") or "").strip()
    instagram = (item.get("instagram") or "").strip()
    facebook = (item.get("facebook") or "").strip()

    links = []

    def add(url, icon):
        if not url:
            return
        norm = url.rstrip("/").lower()
        if norm in seen_urls:
            return
        seen_urls.add(norm)
        links.append(f"{icon} {url}")

    add(website, "🌐")

    if instagram:
        add(instagram, "📸")
    elif facebook:
        add(facebook, "📘")

    return "\n".join(links)


def _inject_links(text: str, items: list, user_input: str) -> str:
    FOOTER = "💚 Small actions create real impact."

    text = (text or "").replace(FOOTER, "").strip()

    def _strip_links(block: str) -> str:
        lines = block.split("\n")
        return "\n".join(
            l for l in lines
            if not l.strip().startswith(("🌐", "📸", "📘"))
        ).strip()

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

    org_blocks = [
        b for b in result_blocks
        if b.strip().startswith(("1.", "2.", "3."))
    ][:3]

    while len(org_blocks) < 3:
        org_blocks.append("")

    seen_urls = set()
    final = []

    for i, item in enumerate(items[:MAX_ITEMS]):
        block = org_blocks[i] if i < len(org_blocks) else ""
        block = _strip_links(block)

        links = _format_links(item, seen_urls)

        if links:
            block += "\n\n" + links

        final.append(block.strip())

    result = "\n\n\n".join(final).strip()

    return result + "\n\n" + FOOTER


def synthesize_answer(user_input, local_data, web_data):
    data = local_data if local_data else web_data if web_data else []

    if not data:
        return "No initiatives found."

    items = data[:MAX_ITEMS]

    while len(items) < MAX_ITEMS:
        items.append({})

    intro = _build_intro(user_input)

    text = intro + "\n\n"

    seen_urls = set()

    for i, item in enumerate(items, start=1):
        name = item.get("name", "Unknown")
        description = item.get("description", "")

        text += f"{i}. {name}\n{description}"

        links = _format_links(item, seen_urls)
        if links:
            text += "\n\n" + links

        text += "\n\n"

    text += "💚 Small actions create real impact."

    return text


def _items_payload(items):
    rows = []

    for it in items[:MAX_ITEMS]:
        rows.append({
            "name": it.get("name") or "Unknown",
            "description": (it.get("description") or "").strip(),
            "tags": (it.get("tags") or "").strip(),
            "help_types": (it.get("help_types") or "").strip(),
            "practical_help": (it.get("practical_help") or "").strip(),
            "website": (it.get("website") or "").strip(),
            "instagram": (it.get("instagram") or "").strip(),
            "facebook": (it.get("facebook") or "").strip(),
        })

    return json.dumps(rows, ensure_ascii=False, indent=2)


def synthesize_advisory(
    user_input,
    local_data,
    web_data,
    user_id=None,
):

    # 🔴 FIX 4 — SAFETY FALLBACK
    if _is_noise_input(user_input):
        return "I can help with volunteering and community support in Belgrade."

    data = local_data if local_data else web_data if web_data else []

    if not data:
        return "No initiatives found."

    items = list(data[:MAX_ITEMS])

    while len(items) < MAX_ITEMS:
        items.append({})

    organizations_json = _items_payload(items)

    memory_context = ""

    if user_id:
        memory_context = build_context_text(user_id)

    prompt = ADVISORY_SYNTHESIS_PROMPT.format(
        user_input=user_input,
        n=len(items),
        organizations_json=organizations_json,
        memory_context=memory_context,
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