from app.agent.nodes.intent import analyze_intent
from app.agent.nodes.clarify import ask_clarification
from app.agent.nodes.local_search import local_search
from app.agent.nodes.web_search import web_search
from app.agent.nodes.synthesis import synthesize_answer
from app.database.search import random_initiatives


def run_workflow(user_input: str):

    text = user_input.lower().strip()

    # =====================================
    # 1. INTENT (ВСЕГДА ПЕРВЫЙ)
    # =====================================
    intent = analyze_intent(user_input)

    print("INTENT:", intent)

    # =====================================
    # 2. CLARIFICATION (ЕСЛИ НУЖНО)
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
        query=" ".join(keywords)
    )

    print("LOCAL DATA:", local_data)

    # =====================================
    # 4. WEB FALLBACK (ТОЛЬКО ЕСЛИ НЕТ LOCAL)
    # =====================================
    web_data = None

    if not local_data:
        web_data = web_search(user_input)

    # =====================================
    # 5. FINAL ANSWER
    # =====================================
    return synthesize_answer(
        user_input=user_input,
        local_data=local_data,
        web_data=web_data
    )