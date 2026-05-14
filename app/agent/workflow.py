from app.agent.nodes.intent import analyze_intent
from app.agent.nodes.clarify import ask_clarification
from app.agent.nodes.local_search import local_search, random_initiatives
from app.agent.nodes.web_search import web_search
from app.agent.nodes.synthesis import synthesize_advisory
from app.utils.logger import logger


def _web_results_as_items(web_data, exclude_urls=None, max_raw=15):
    if not web_data or not isinstance(web_data, dict):
        return []

    raw = web_data.get("results") or []

    items = []

    for r in raw[:max_raw]:
        if not isinstance(r, dict):
            continue

        items.append({
            "name": r.get("name", "Web result"),
            "description": r.get("description", ""),
            "website": r.get("website", ""),
            "instagram": "",
            "facebook": "",
            "_source": "web",
        })

    return items


def _dedupe(items):
    seen = set()
    out = []

    for i in items:
        key = (i.get("name") or i.get("website") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(i)

    return out


def _should_fallback(local_data):
    return len(local_data or []) < 2


def _fetch_web(user_input, replay):

    query_map = {
        "preset_category": f"{user_input} NGO volunteer Serbia Belgrade",
        "mixed_random": f"{user_input} volunteer help Serbia NGO",
        "freeform": f"{user_input} NGO volunteer help",
    }

    q = query_map.get(replay.get("kind"), f"{user_input} NGO volunteer")

    logger.info(f"[WF WEB CALL] query={q}")

    return web_search(q)


def _answer(user_input, local_data, web_data, replay):

    logger.info(f"[WF ANSWER] local={len(local_data or [])} web={bool(web_data)}")

    local_items = local_data or []
    web_items = _web_results_as_items(web_data)

    data = _dedupe(local_items + web_items)

    logger.info(f"[WF FINAL ITEMS] {len(data)}")

    if not data:
        return {
            "type": "answer",
            "text": "No initiatives found.",
            "items": [],
            "replay": replay,
        }

    text = synthesize_advisory(user_input, local_items, web_items)

    return {
        "type": "answer",
        "text": text,
        "items": data,
        "replay": replay,
    }


def run_workflow(user_input, exclude_names=None, exclude_urls=None):

    logger.info(f"[WF INPUT] {user_input}")

    text = user_input.lower().strip()

    if "help animals" in text or "🐾" in text:
        category = "animals"
        query = "cats dogs rescue"

    elif "help environment" in text or "🌍" in text:
        category = "environment"
        query = "cleanup trees ecology"

    elif "help people" in text or "🤝" in text:
        category = "community"
        query = "community homeless elderly"

    elif "suggest" in text or "good deed" in text:
        category = None
        query = None

    else:
        intent = analyze_intent(user_input)
        category = intent.get("category")
        query = " ".join(intent.get("keywords", []))

        if intent.get("needs_clarification"):
            return ask_clarification(intent)

    local_data = local_search(category, query, exclude_names)

    logger.info(f"[WF LOCAL] {len(local_data)}")

    replay = {
        "kind": "freeform",
        "user_input": user_input,
        "category": category
    }

    web_data = None

    if _should_fallback(local_data):
        web_data = _fetch_web(user_input, replay)

    return _answer(user_input, local_data, web_data, replay)


def repeat_last_search(replay, exclude_names=None, exclude_urls=None):

    if not replay:
        return None

    return run_workflow(
        replay.get("user_input", ""),
        exclude_names,
        exclude_urls
    )