from app.agent.nodes.intent import analyze_intent
from app.agent.nodes.clarify import ask_clarification
from app.agent.nodes.local_search import local_search
from app.agent.nodes.web_search import web_search
from app.agent.nodes.synthesis import synthesize_advisory


def _norm_url(u: str | None) -> str:
    if not u:
        return ""
    return str(u).strip().lower().rstrip("/")


def _web_results_as_items(
    web_data,
    exclude_urls: list | None = None,
    max_raw: int = 15,
):
    excluded = {_norm_url(u) for u in (exclude_urls or []) if u}
    if not web_data or not isinstance(web_data, dict):
        return []
    raw = web_data.get("results") or []
    items = []
    for r in raw[:max_raw]:
        if not isinstance(r, dict):
            continue
        url = r.get("url") or ""
        if _norm_url(url) in excluded:
            continue
        title = (r.get("title") or "").strip() or url or "Web result"
        desc = (r.get("content") or "").strip()
        items.append(
            {
                "name": title,
                "description": desc,
                "website": url or None,
                "instagram": None,
                "facebook": None,
                "tags": "",
                "help_types": "",
                "practical_help": "",
                "_source": "web",
            }
        )
    return items


def _build_web_query(user_input: str, replay: dict) -> str:
    kind = replay.get("kind")
    if kind == "preset_category":
        cat = replay.get("category", "")
        return f"{user_input} {cat} volunteer donate charity NGO Serbia Belgrade"
    if kind == "mixed_random":
        return f"{user_input} volunteer good deeds charity help Serbia Belgrade"
    if kind == "freeform":
        return f"{replay.get('user_input', user_input)} volunteer charity help Serbia"
    return f"{user_input} volunteer charity Serbia Belgrade"


def _fetch_web_fallback(
    user_input: str,
    replay: dict,
    exclude_urls: list | None,
):
    q = _build_web_query(user_input, replay)
    web_data = web_search(q)
    if _web_results_as_items(web_data, exclude_urls=exclude_urls):
        return web_data
    return web_search(q + " organizations")


def _answer_dict(
    user_input,
    local_data,
    web_data,
    replay: dict,
    exclude_urls: list | None = None,
):
    web_items = _web_results_as_items(web_data, exclude_urls=exclude_urls)

    if local_data:
        data = []
        for row in local_data:
            d = dict(row)
            d["_source"] = "local"
            data.append(d)
        web_for_synth = None
    else:
        data = web_items
        web_for_synth = web_items if web_items else None

    if not data:
        return {
            "type": "answer",
            "text": "No initiatives found.",
            "items": [],
            "replay": replay,
        }

    text = synthesize_advisory(
        user_input,
        local_data if local_data else None,
        web_for_synth,
    )
    items = [dict(r) for r in data]
    return {"type": "answer", "text": text, "items": items, "replay": replay}


def run_workflow(
    user_input: str,
    exclude_names: list | None = None,
    exclude_urls: list | None = None,
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
        web_data = None
        if not local_data:
            web_data = _fetch_web_fallback(
                user_input, replay, exclude_urls
            )
        return _answer_dict(
            user_input, local_data, web_data, replay, exclude_urls=exclude_urls
        )

    # 🌍 Environment
    if "help environment" in text or "🌍" in text:
        category = "Environment"
        query_str = "environment cleanup trees ecology"
        local_data = local_search(
            category=category,
            query=query_str,
            exclude_names=exclude_names,
        )
        replay = {
            "kind": "preset_category",
            "category": category,
            "query": query_str,
        }
        web_data = None
        if not local_data:
            web_data = _fetch_web_fallback(
                user_input, replay, exclude_urls
            )
        return _answer_dict(
            user_input, local_data, web_data, replay, exclude_urls=exclude_urls
        )

    # 🤝 Community — не пересекать ветку "community" в тексте до intent (кнопка 🤝)
    if "help people" in text or "🤝" in text:
        category = "Community"
        query_str = "community homeless elderly refugees"
        local_data = local_search(
            category=category,
            query=query_str,
            exclude_names=exclude_names,
        )
        replay = {
            "kind": "preset_category",
            "category": category,
            "query": query_str,
        }
        web_data = None
        if not local_data:
            web_data = _fetch_web_fallback(
                user_input, replay, exclude_urls
            )
        return _answer_dict(
            user_input, local_data, web_data, replay, exclude_urls=exclude_urls
        )

    # Свободный "community" в тексте (без кнопки людей)
    if "community" in text:
        category = "Community"
        query_str = "community homeless elderly refugees"
        local_data = local_search(
            category=category,
            query=query_str,
            exclude_names=exclude_names,
        )
        replay = {
            "kind": "preset_category",
            "category": category,
            "query": query_str,
        }
        web_data = None
        if not local_data:
            web_data = _fetch_web_fallback(
                user_input, replay, exclude_urls
            )
        return _answer_dict(
            user_input, local_data, web_data, replay, exclude_urls=exclude_urls
        )

    # 🌱 Suggest random deed
    if "suggest" in text or "good deed" in text:
        local_data = local_search(
            category="mixed",
            query="random",
            exclude_names=exclude_names,
        )
        replay = {"kind": "mixed_random"}
        web_data = None
        if not local_data:
            web_data = _fetch_web_fallback(
                user_input, replay, exclude_urls
            )
        return _answer_dict(
            user_input, local_data, web_data, replay, exclude_urls=exclude_urls
        )

    intent = analyze_intent(user_input)
    print("INTENT:", intent)

    if intent.get("needs_clarification"):
        return ask_clarification(intent)

    category = intent.get("category")
    keywords = intent.get("keywords", [])
    local_data = local_search(
        category=category,
        query=" ".join(keywords),
        exclude_names=exclude_names,
    )
    print("LOCAL DATA:", local_data)

    web_data = None
    if not local_data:
        replay = {"kind": "freeform", "user_input": user_input}
        web_data = _fetch_web_fallback(user_input, replay, exclude_urls)
        return _answer_dict(
            user_input, local_data, web_data, replay, exclude_urls=exclude_urls
        )

    replay = {"kind": "freeform", "user_input": user_input}
    return _answer_dict(
        user_input, local_data, web_data, replay, exclude_urls=exclude_urls
    )


def repeat_last_search(
    replay: dict | None,
    exclude_names: list[str] | None,
    exclude_urls: list[str] | None = None,
):
    if not replay:
        return None
    kind = replay.get("kind")
    if kind == "preset_category":
        category = replay.get("category")
        query = replay.get("query")
        local_data = local_search(
            category=category, query=query, exclude_names=exclude_names
        )
        web_data = None
        if not local_data:
            web_data = _fetch_web_fallback(
                f"{category}: {query}", replay, exclude_urls
            )
        return _answer_dict(
            user_input=f"{category}: {query}",
            local_data=local_data,
            web_data=web_data,
            replay=replay,
            exclude_urls=exclude_urls,
        )
    if kind == "mixed_random":
        local_data = local_search(
            category="mixed", query="random", exclude_names=exclude_names
        )
        web_data = None
        if not local_data:
            web_data = _fetch_web_fallback(
                "Suggest a good deed", replay, exclude_urls
            )
        return _answer_dict(
            user_input="Suggest a good deed",
            local_data=local_data,
            web_data=web_data,
            replay=replay,
            exclude_urls=exclude_urls,
        )
    if kind == "freeform":
        user_input_val = replay.get("user_input", "")
        return run_workflow(
            user_input_val,
            exclude_names=exclude_names,
            exclude_urls=exclude_urls,
        )
    return None