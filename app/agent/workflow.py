from app.agent.nodes.intent import analyze_intent
from app.agent.nodes.clarify import ask_clarification
from app.agent.nodes.local_search import local_search, random_initiatives
from app.agent.nodes.web_search import web_search
from app.agent.nodes.synthesis import synthesize_advisory


# =====================================
# HELPERS
# =====================================

def _web_results_as_items(web_data, exclude_urls=None, max_raw=15):
    if not web_data or not isinstance(web_data, dict):
        return []

    raw = web_data.get("results") or []
    items = []

    for r in raw[:max_raw]:
        if not isinstance(r, dict):
            continue

        items.append({
            "name": (r.get("title") or "Web result"),
            "description": (r.get("content") or ""),
            "website": r.get("url") or "",
            "instagram": "",
            "facebook": "",
            "_source": "web",
        })

    return items


def _dedupe(items):
    seen = set()
    out = []

    for i in items:
        if not isinstance(i, dict):
            continue

        key = (i.get("name") or i.get("website") or "").strip().lower()
        if not key or key in seen:
            continue

        seen.add(key)
        out.append(i)

    return out


def _should_fallback(local_data):
    """
    SINGLE source of truth for web fallback logic
    """
    return not local_data or len(local_data) < 2


def _fetch_web(user_input, replay):
    query_map = {
        "preset_category": f"{user_input} NGO volunteer Serbia Belgrade",
        "mixed_random": f"{user_input} volunteer help Serbia NGO",
        "freeform": f"{user_input} NGO volunteer help",
    }

    q = query_map.get(replay.get("kind"), f"{user_input} volunteer NGO")

    return web_search(q)


# =====================================
# CORE
# =====================================

def _answer(user_input, local_data, web_data, replay):
    local_items = local_data or []
    web_items = _web_results_as_items(web_data)

    data = _dedupe(local_items + web_items)

    if not data:
        return {
            "type": "answer",
            "text": "No initiatives found.",
            "items": [],
            "replay": replay,
        }

    text = synthesize_advisory(
        user_input,
        local_items if local_items else None,
        web_items if web_items else None,
    )

    return {
        "type": "answer",
        "text": text,
        "items": data,
        "replay": replay,
    }


# =====================================
# WORKFLOW
# =====================================

def run_workflow(user_input, exclude_names=None, exclude_urls=None):
    text = user_input.lower().strip()

    # -------------------------
    # FAST PATHS
    # -------------------------

    if "help animals" in text or "🐾" in text:
        category = "Animals"
        query = "cats dogs rescue stray animals"

        local_data = local_search(category, query, exclude_names)
        replay = {"kind": "preset_category", "category": category}

        web_data = _fetch_web(user_input, replay) if _should_fallback(local_data) else None
        return _answer(user_input, local_data, web_data, replay)

    if "help environment" in text or "🌍" in text:
        category = "Environment"
        query = "cleanup trees ecology"

        local_data = local_search(category, query, exclude_names)
        replay = {"kind": "preset_category", "category": category}

        web_data = _fetch_web(user_input, replay) if _should_fallback(local_data) else None
        return _answer(user_input, local_data, web_data, replay)

    if "help people" in text or "🤝" in text:
        category = "Community"
        query = "community homeless elderly refugees"

        local_data = local_search(category, query, exclude_names)
        replay = {"kind": "preset_category", "category": category}

        web_data = _fetch_web(user_input, replay) if _should_fallback(local_data) else None
        return _answer(user_input, local_data, web_data, replay)

    if "suggest" in text or "good deed" in text:
        local_data = random_initiatives(limit=5, category=None, exclude_names=exclude_names)
        replay = {"kind": "mixed_random"}

        web_data = _fetch_web(user_input, replay) if _should_fallback(local_data) else None
        return _answer(user_input, local_data, web_data, replay)

    # -------------------------
    # INTENT FLOW
    # -------------------------

    intent = analyze_intent(user_input)

    if intent.get("needs_clarification"):
        return ask_clarification(intent)

    category = intent.get("category")
    keywords = intent.get("keywords", [])

    local_data = local_search(category, " ".join(keywords), exclude_names)

    replay = {"kind": "freeform", "user_input": user_input}

    web_data = _fetch_web(user_input, replay) if _should_fallback(local_data) else None

    return _answer(user_input, local_data, web_data, replay)


# =====================================
# REPEAT
# =====================================

def repeat_last_search(replay, exclude_names=None, exclude_urls=None):
    if not replay:
        return None

    kind = replay.get("kind")

    if kind == "preset_category":
        category = replay.get("category")

        local_data = local_search(category, replay.get("query"), exclude_names)
        web_data = _fetch_web(replay.get("query", ""), replay) if _should_fallback(local_data) else None

        return _answer(replay.get("query", ""), local_data, web_data, replay)

    if kind == "mixed_random":
        local_data = random_initiatives(limit=5, category=None, exclude_names=exclude_names)
        web_data = _fetch_web("good deed", replay) if _should_fallback(local_data) else None

        return _answer("good deed", local_data, web_data, replay)

    if kind == "freeform":
        return run_workflow(
            replay.get("user_input", ""),
            exclude_names,
            exclude_urls,
        )

    return None