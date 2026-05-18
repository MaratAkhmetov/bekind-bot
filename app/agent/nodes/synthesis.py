import json
import re

from app.agent.prompts import (
    ADVISORY_SYNTHESIS_PROMPT,
    INTRO_PROMPT,
)

from app.services.llm import generate_text

from app.agent.memory import build_context_text

MAX_ITEMS = 3


def _build_intro(user_input: str) -> str:
    try:
        prompt = INTRO_PROMPT.format(user_input=user_input)
        
        out = generate_text(prompt)
        
        if out and str(out).strip():
            intro = str(out).strip()
            
            intro = intro.replace("\n", " ").strip()
            
            intro = intro.strip('"').strip("'").strip()
            
            if intro.endswith('".'):
                intro = intro[:-2]
            
            if intro.endswith("'."):
                intro = intro[:-2]
            
            intro = intro.replace("*", "")
            intro = intro.replace("**", "")
            intro = intro.replace("_", "")
            
            intro = re.sub(r"\s+", " ", intro).strip()
            intro = re.sub(r"[\"'`]", "", intro)
            
            if not intro.endswith((".", "!", "?")):
                intro += "."
            
            intro = intro.replace("*", "").replace("#", "")
            
            return intro
    
    except Exception:
        pass
    
    text = user_input.lower()
    
    if "animal" in text or "🐾" in text:
        return "Here are some ways you can help animals in Belgrade."
    
    if "environment" in text or "🌍" in text:
        return "If you'd like to support the environment, here are a few real initiatives."
    
    if "community" in text or "people" in text:
        return "Here are meaningful ways to help people in your community."
    
    return "Here are real ways you can make a positive impact."


def _format_links(item: dict) -> str:
    website = item.get("website")
    instagram = item.get("instagram")
    facebook = item.get("facebook")
    
    links = []
    
    if website:
        links.append(f"🌐 {website}")
    
    if instagram:
        links.append(f"📸 {instagram}")
    
    elif facebook:
        links.append(f"📘 {facebook}")
    
    return "\n".join(links)


def _inject_links(
    text: str,
    items: list,
    user_input: str,
) -> str:
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
        if any(
            b.strip().startswith(f"{i}.")
            for i in range(1, 10)
        ):
            org_blocks.append(b)
    
    org_blocks = org_blocks[:3]
    
    while len(org_blocks) < 3:
        org_blocks.append("")
    
    final = []
    
    for i, item in enumerate(items[:MAX_ITEMS]):
        block = org_blocks[i] if i < len(org_blocks) else ""
        
        links = _format_links(item)
        
        if links:
            block += "\n\n" + links
        
        final.append(block.strip())
    
    result = "\n\n\n".join(final).strip()
    
    first_line = result.split("\n", 1)[0].strip() if result else ""
    
    if first_line and not first_line.startswith(("1.", "2.", "3.")):
        cleaned_intro = first_line.strip().strip('"').strip("'").strip()
        
        if cleaned_intro.endswith('".'):
            cleaned_intro = cleaned_intro[:-2]
        
        if cleaned_intro.endswith("'."):
            cleaned_intro = cleaned_intro[:-2]
        
        remaining = result.split("\n", 1)
        
        if len(remaining) > 1:
            result = cleaned_intro + "\n" + remaining[1]
        else:
            result = cleaned_intro
    
    first_line = result.split("\n", 1)[0].strip() if result else ""
    
    if first_line.startswith(("1.", "2.", "3.")):
        intro = _build_intro(user_input)
        
        result = intro + "\n\n" + result
    
    return result + "\n\n" + FOOTER


def synthesize_answer(
    user_input,
    local_data,
    web_data,
):
    data = local_data if local_data else web_data if web_data else []
    
    if not data:
        return "No initiatives found."
    
    items = data[:MAX_ITEMS]
    
    while len(items) < MAX_ITEMS:
        items.append({})
    
    intro = _build_intro(user_input)
    
    text = intro + "\n\n"
    
    for i, item in enumerate(items, start=1):
        name = item.get("name", "Unknown")
        
        description = item.get("description", "")
        
        text += f"{i}. {name}\n"
        text += f"{description}"
        
        links = _format_links(item)
        
        if links:
            text += "\n\n" + links
        
        text += "\n\n"
    
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


def synthesize_advisory(
    user_input,
    local_data,
    web_data,
    user_id=None,
):
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