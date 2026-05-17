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


def _should_fallback(local_data):
    return len(local_data or []) < 2


def _fetch_web(user_input, replay):

    base_geo = "Belgrade Serbia"

    q = f"{user_input} volunteering NGOs {base_geo}"

    logger.info(f"[WF WEB CALL] query={q}")

    return web_search(q)


# =========================
# FIXED: NO FLATTENING HERE
# =========================
def _answer(user_input, local_data, web_data, replay):

    logger.info(f"[WF ANSWER] web={bool(web_data)}")

    web_items = _web_results_as_items(web_data)

    # ALWAYS KEEP STRUCTURE
    if not isinstance(local_data, dict):
        structured_local = {
            "animals": local_data or [],
            "environment": [],
            "community": []
        }
    else:
        structured_local = local_data

    logger.info(
        f"[WF STRUCTURE] "
        f"a={len(structured_local.get('animals', []))} "
        f"e={len(structured_local.get('environment', []))} "
        f"c={len(structured_local.get('community', []))}"
    )

    return {
        "type": "answer",
        "text": synthesize_advisory(
            user_input,
            structured_local,   # ✅ IMPORTANT
            web_items
        ),
        "items": structured_local,  # ✅ IMPORTANT
        "replay": replay,
    }


def run_workflow(user_input, exclude_names=None, exclude_urls=None):

    logger.info(f"[WF INPUT] {user_input}")

    intent = analyze_intent(user_input)

    logger.info(f"[WF INTENT] {intent}")

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

    category = str(intent.get("category", "")).lower()
    query = " ".join(intent.get("keywords", []))

    replay = {
        "kind": "freeform",
        "user_input": user_input,
        "category": category,
    }

    local_data = None
    web_data = None

    # =========================
    # RANDOM GOOD DEED FIX (MAIN ISSUE AREA)
    # =========================
    if category == "random_good_deed":

        logger.info("[WF RANDOM GOOD DEED MODE]")

        local_data = {
            "animals": local_search("animals", query, exclude_names),
            "environment": local_search("environment", query, exclude_names),
            "community": local_search("community", query, exclude_names),
        }

        total = (
            len(local_data["animals"])
            + len(local_data["environment"])
            + len(local_data["community"])
        )

        # fallback ONLY if weak coverage
        if total < 2:
            web_data = _fetch_web(user_input, replay)

    else:

        local_data = local_search(category, query, exclude_names)

        if _should_fallback(local_data):
            web_data = _fetch_web(user_input, replay)

    # clarify ONLY for unclear
    if should_clarify(intent) and category == "unclear":
        return ask_clarification(intent, user_input)

    return _answer(
        user_input,
        local_data,
        web_data,
        replay
    )


def repeat_last_search(replay, exclude_names=None, exclude_urls=None):

    if not replay:
        return None

    return run_workflow(
        replay.get("user_input", ""),
        exclude_names,
        exclude_urls
    )