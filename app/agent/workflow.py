from app.agent.nodes.intent import analyze_intent
from app.agent.nodes.clarify import ask_clarification
from app.agent.nodes.local_search import local_search
from app.agent.nodes.web_search import web_search
from app.agent.nodes.synthesis import synthesize_answer

def _web_results_as_items(web_data):
    """
    Превращает ответ web_search() в список dict как у initiatives.
    Адаптируйте ключи если у Tavily или вашего web_data иные.
    """
    if not web_data or not isinstance(web_data, dict):
        return []
    raw = web_data.get("results") or []
    items = []
    for r in raw[:5]:
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
        })
    return items

def _answer_dict(user_input, local_data, web_data, replay: dict):
    web_items = _web_results_as_items(web_data)
    if local_data:
        data = local_data
        web_for_synth = None
    else:
        data = web_items
        web_for_synth = web_items if web_items else None

    if not data:
        return {"type": "answer", "text": "No initiatives found.", "items": [], "replay": replay}
    items = list(data[:5])
    text = synthesize_answer(user_input, local_data if local_data else None, web_for_synth)
    return {"type": "answer", "text": text, "items": items, "replay": replay}

def run_workflow(user_input: str, exclude_names: list | None = None):
    text = user_input.lower().strip()

    # 🐾 Animals button
    if "help animals" in text or "🐾" in text:
        category = "Animals"
        query_str = "cats dogs stray animals rescue"
        local_data = local_search(
            category=category,
            query=query_str,
            exclude_names=exclude_names
        )
        replay = {"kind": "preset_category", "category": category, "query": query_str}
        return _answer_dict(user_input, local_data, None, replay)

    # 🌍 Environment button
    if "help environment" in text or "🌍" in text:
        category = "Environment"
        query_str = "environment cleanup trees ecology"
        local_data = local_search(
            category=category,
            query=query_str,
            exclude_names=exclude_names
        )
        replay = {"kind": "preset_category", "category": category, "query": query_str}
        return _answer_dict(user_input, local_data, None, replay)

    # 🤝 Community button
    if "help people" in text or "community" in text or "🤝" in text:
        category = "Community"
        query_str = "community homeless elderly refugees"
        local_data = local_search(
            category=category,
            query=query_str,
            exclude_names=exclude_names
        )
        replay = {"kind": "preset_category", "category": category, "query": query_str}
        return _answer_dict(user_input, local_data, None, replay)

    # 🌱 Suggest random deed
    if "suggest" in text or "good deed" in text:
        local_data = local_search(
            category="mixed",
            query="random",
            exclude_names=exclude_names
        )
        replay = {"kind": "mixed_random"}
        return _answer_dict(user_input, local_data, None, replay)

    # =====================================
    # 1. INTENT ANALYSIS
    # =====================================
    intent = analyze_intent(user_input)
    print("INTENT:", intent)

    # =====================================
    # 2. CLARIFICATION
    # =====================================
    if intent.get("needs_clarification"):
        return ask_clarification(intent)

    # =====================================
    # 3. LOCAL SEARCH
    # =====================================
    category = intent.get("category")
    keywords = intent.get("keywords", [])
    local_data = local_search(
        category=category,
        query=" ".join(keywords),
        exclude_names=exclude_names
    )
    print("LOCAL DATA:", local_data)

    # =====================================
    # 4. WEB FALLBACK
    # =====================================
    web_data = None
    if not local_data:
        web_data = web_search(user_input)

    # =====================================
    # 5. FINAL ANSWER
    # =====================================
    replay = {"kind": "freeform", "user_input": user_input}
    return _answer_dict(user_input, local_data, web_data, replay)

def repeat_last_search(replay: dict | None, exclude_names: list[str] | None):
    if not replay:
        return None
    kind = replay.get("kind")
    if kind == "preset_category":
        category = replay.get("category")
        query = replay.get("query")
        local_data = local_search(category=category, query=query, exclude_names=exclude_names)
        return _answer_dict(
            user_input=f"{category}: {query}",
            local_data=local_data,
            web_data=None,
            replay=replay
        )
    elif kind == "mixed_random":
        local_data = local_search(category="mixed", query="random", exclude_names=exclude_names)
        return _answer_dict(
            user_input="Suggest a good deed",
            local_data=local_data,
            web_data=None,
            replay=replay
        )
    elif kind == "freeform":
        user_input_val = replay.get("user_input", "")
        return run_workflow(user_input_val, exclude_names=exclude_names)
    # fallback
    return None