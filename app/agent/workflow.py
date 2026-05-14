from app.agent.nodes.intent import analyze_intent
from app.agent.nodes.clarify import ask_clarification
from app.agent.nodes.local_search import local_search, random_initiatives
from app.agent.nodes.web_search import web_search
from app.agent.nodes.synthesis import synthesize_advisory


# =====================================
# HELPERS
# =====================================

def _norm_url(u: str | None) -> str:
    if not u:
        return ""
    return str(u).strip().lower().rstrip("/")


def _web_results_as_items(web_data, exclude_urls=None, max_raw=15):
    excluded = {_norm_url(u) for u in (exclude_urls or [])}

    if not web_data or not isinstance(web_data, dict):
        return []

    raw = web_data.get("results") or []
    items = []

    for r in raw[:max_raw]:
        if not isinstance(r, dict):
            continue

        url = r.get("url") or ""
        title = (r.get("title") or "").strip() or url or "Web result"
        desc = (r.get("content") or "").strip()

        items.append({
            "name": title,
            "description": desc,
            "website": url or None,
            "instagram": None,
            "facebook": None,
            "tags": "",
            "help_types": "",
            "practical_help": "",
            "_source": "web",
        })

    return items


def _dedupe(items):
    seen = set()
    result = []

    for i in items:
        if not isinstance(i, dict):
            continue

        name = (i.get("name") or "").strip().lower()
        url = _norm_url(i.get("website"))

        key = name or url
        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        result.append(i)

    return result


def _build_web_query(user_input: str, replay: dict) -> str:
    kind = replay.get("kind")

    if kind == "preset_category":
        cat = replay.get("category", "")
        return f"{user_input} {cat} volunteer NGO charity Serbia Belgrade"

    if kind == "mixed_random":
        return f"{user_input} volunteer help charity Serbia initiatives"

    if kind == "freeform":
        return f"{replay.get('user_input', user_input)} NGO volunteer help Serbia"

    return f"{user_input} volunteer NGO Serbia"


def _fetch_web_fallback(user_input: str, replay: dict, exclude_urls=None):
    q = _build_web_query(user_input, replay)

    web_data = web_search(q)

    if _web_results_as_items(web_data, exclude_urls):
        return web_data

    return web_search(q + " organizations volunteer NGO")


# =====================================
# CORE ANSWER BUILDER
# =====================================

def _answer_dict(
    user_input,
    local_data,
    web_data,
    replay: dict,
    exclude_urls=None,
):

    local_items = []
    if local_data:
        for row in local_data:
            d = dict(row)
            d["_source"] = "local"
            local_items.append(d)

    web_items = _web_results_as_items(web_data, exclude_urls=exclude_urls)

    # MERGE EVERYTHING
    data = _dedupe(local_items + web_items)

    if not data:
        return {
            "type": "answer",
            "text": "No initiatives found.",
            "items": [],
            "replay": replay,
        }

    # synthesis prefers local+web if available
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
# MAIN WORKFLOW
# =====================================

def run_workflow(
    user_input: str,
    exclude_names=None,
    exclude_urls=None,
):
    text = user_input.lower().strip()

    # 🐾 Animals
    if "help animals" in text or "🐾" in text:
        category = "Animals"
        query_str = "cats dogs stray animals rescue"

        local_data = local_search(
            category=category,
            query=query_str,
            exclude_names=exclude_names,
        )

        replay = {"kind": "preset_category", "category": category, "query": query_str}

        web_data = _fetch_web_fallback(user_input, replay, exclude_urls)

        return _answer_dict(user_input, local_data, web_data, replay, exclude_urls)

    # 🌍 Environment
    if "help environment" in text or "🌍" in text:
        category = "Environment"
        query_str = "environment cleanup trees ecology"

        local_data = local_search(
            category=category,
            query=query_str,
            exclude_names=exclude_names,
        )

        replay = {"kind": "preset_category", "category": category, "query": query_str}

        web_data = _fetch_web_fallback(user_input, replay, exclude_urls)

        return _answer_dict(user_input, local_data, web_data, replay, exclude_urls)

    # 🤝 Community
    if "help people" in text or "🤝" in text:
        category = "Community"
        query_str = "community homeless elderly refugees"

        local_data = local_search(
            category=category,
            query=query_str,
            exclude_names=exclude_names,
        )

        replay = {"kind": "preset_category", "category": category, "query": query_str}

        web_data = _fetch_web_fallback(user_input, replay, exclude_urls)

        return _answer_dict(user_input, local_data, web_data, replay, exclude_urls)

    # 🌱 Suggest random deed
    if "suggest" in text or "good deed" in text:
        local_data = random_initiatives(
            limit=3,
            category=None,
            exclude_names=exclude_names,
        )

        replay = {"kind": "mixed_random"}

        web_data = _fetch_web_fallback(user_input, replay, exclude_urls)

        return _answer_dict(user_input, local_data, web_data, replay, exclude_urls)

    # INTENT FLOW
    intent = analyze_intent(user_input)

    if intent.get("needs_clarification"):
        return ask_clarification(intent)

    category = intent.get("category")
    keywords = intent.get("keywords", [])

    local_data = local_search(
        category=category,
        query=" ".join(keywords),
        exclude_names=exclude_names,
    )

    replay = {"kind": "freeform", "user_input": user_input}

    web_data = None
    if not local_data:
        web_data = _fetch_web_fallback(user_input, replay, exclude_urls)

    return _answer_dict(user_input, local_data, web_data, replay, exclude_urls)


# =====================================
# REPEAT SEARCH
# =====================================

def repeat_last_search(
    replay: dict | None,
    exclude_names=None,
    exclude_urls=None,
):
    if not replay:
        return None

    kind = replay.get("kind")

    if kind == "preset_category":
        category = replay.get("category")
        query = replay.get("query")

        local_data = local_search(
            category=category,
            query=query,
            exclude_names=exclude_names,
        )

        web_data = _fetch_web_fallback(
            f"{category}: {query}",
            replay,
            exclude_urls,
        )

        return _answer_dict(
            f"{category}: {query}",
            local_data,
            web_data,
            replay,
            exclude_urls,
        )

    if kind == "mixed_random":
        local_data = random_initiatives(
            limit=3,
            category=None,
            exclude_names=exclude_names,
        )

        web_data = _fetch_web_fallback(
            "Suggest a good deed",
            replay,
            exclude_urls,
        )

        return _answer_dict(
            "Suggest a good deed",
            local_data,
            web_data,
            replay,
            exclude_urls,
        )

    if kind == "freeform":
        return run_workflow(
            replay.get("user_input", ""),
            exclude_names=exclude_names,
            exclude_urls=exclude_urls,
        )

    return None