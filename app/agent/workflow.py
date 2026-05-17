from app.agent.nodes.intent import analyze_intent
from app.agent.nodes.clarify import (
    ask_clarification,
    should_clarify,
)

from app.agent.nodes.local_search import local_search
from app.agent.nodes.web_search import web_search
from app.agent.nodes.synthesis import synthesize_advisory
from app.utils.logger import logger


BELGRADE_HINTS = [
    "serbia",
    "belgrade",
    "beograd",
    "rs",
]


def _web_results_as_items(web_data, exclude_urls=None, max_raw=15):

    if not web_data or not isinstance(web_data, dict):
        return []

    raw = web_data.get("results") or []

    items = []

    for r in raw[:max_raw]:

        if not isinstance(r, dict):
            continue

        text_blob = " ".join([
            str(r.get("name", "")),
            str(r.get("description", "")),
            str(r.get("website", "")),
        ]).lower()

        if not any(hint in text_blob for hint in BELGRADE_HINTS):
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

        key = (
            (i.get("name") or "").strip().lower(),
            (i.get("website") or "").strip().lower()
        )

        if key in seen:
            continue

        seen.add(key)
        out.append(i)

    return out


def _should_fallback(local_data):
    return len(local_data or []) < 2


def _fetch_web(user_input, replay):

    base_geo = "Belgrade Serbia"

    query_map = {
        "preset_category": f"{user_input} volunteer NGO {base_geo}",
        "mixed_random": f"{user_input} charities volunteering {base_geo}",
        "freeform": f"{user_input} NGO volunteering organizations {base_geo}",
    }

    q = query_map.get(
        replay.get("kind"),
        f"{user_input} volunteer NGO {base_geo}"
    )

    logger.info(f"[WF WEB CALL GEO] query={q}")

    return web_search(q)


def _answer(user_input, local_data, web_data, replay):

    logger.info(
        f"[WF ANSWER] local={len(local_data or {})} web={bool(web_data)}"
    )

    # =========================
    # FIX: support structured local_data
    # =========================
    if isinstance(local_data, dict):
        local_items = (
            local_data.get("animals", [])
            + local_data.get("environment", [])
            + local_data.get("community", [])
        )
    else:
        local_items = local_data or []

    web_items = _web_results_as_items(web_data)

    # FIX: DO NOT flatten before dedupe incorrectly
    data = _dedupe(local_items) + web_items

    logger.info(f"[WF FINAL ITEMS] {len(data)}")

    # UX fallback
    if not data:
        return {
            "type": "answer",
            "text": "I couldn’t find exact matches, but here are some nearby ways to help.",
            "items": [],
            "replay": replay,
        }

    text = synthesize_advisory(
        user_input,
        local_items,
        web_items
    )

    return {
        "type": "answer",
        "text": text,
        "items": data,
        "replay": replay,
    }


def run_workflow(user_input, exclude_names=None, exclude_urls=None):

    logger.info(f"[WF INPUT] {user_input}")

    intent = analyze_intent(user_input)

    logger.info(f"[WF INTENT] {intent}")

    # FIX: soft invalid guard
    if intent.get("is_invalid") and not intent.get("needs_clarification"):
        return {
            "type": "answer",
            "text": (
                "I can only help with volunteering, animals, environment, "
                "and community support in Belgrade."
            ),
            "items": [],
            "replay": None,
        }

    # FIX: normalize category
    category = str(intent.get("category", "")).lower()

    query = " ".join(intent.get("keywords", []))

    replay = {
        "kind": "freeform",
        "user_input": user_input,
        "category": category,
    }

    local_data = {}

    # =========================
    # RANDOM GOOD DEED FIXED STRUCTURE
    # =========================
    if category == "random_good_deed":

        logger.info("[WF RANDOM GOOD DEED MODE]")

        local_data = {
            "animals": local_search("animals", query, exclude_names),
            "environment": local_search("environment", query, exclude_names),
            "community": local_search("community", query, exclude_names),
        }

        # ONLY check for web fallback (DO NOT mix into categories)
        total_local = (
            len(local_data["animals"])
            + len(local_data["environment"])
            + len(local_data["community"])
        )

        if total_local < 2:
            web_data = _fetch_web(user_input, replay)
        else:
            web_data = None

    else:
        local_data = local_search(category, query, exclude_names)

        web_data = None

        # fallback enrichment allowed for all non-random cases
        if _should_fallback(local_data):
            web_data = _fetch_web(user_input, replay)

    logger.info(f"[WF LOCAL] {len(local_data) if isinstance(local_data, list) else 'structured'}")

    # clarify ONLY for unclear + no data
    if (
        should_clarify(intent)
        and (not local_data or (isinstance(local_data, list) and len(local_data) == 0))
        and category == "unclear"
    ):
        return ask_clarification(intent, user_input)

    return _answer(
        user_input,
        local_data,
        web_data,
        replay
    )


def repeat_last_search(
    replay,
    exclude_names=None,
    exclude_urls=None
):

    if not replay:
        return None

    return run_workflow(
        replay.get("user_input", ""),
        exclude_names,
        exclude_urls
    )