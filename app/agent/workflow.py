from app.agent.nodes.intent import analyze_intent
from app.agent.nodes.clarify import ask_clarification
from app.agent.nodes.local_search import local_search
from app.agent.nodes.web_search import web_search
from app.agent.nodes.synthesis import synthesize_answer


def run_workflow(user_input: str):

    text = user_input.lower().strip()

    # 🐾 Animals button
    if "help animals" in text or "🐾" in text:

        local_data = local_search(
            category="Animals",
            query="cats dogs stray animals rescue"
        )

        return synthesize_answer(
            user_input=user_input,
            local_data=local_data,
            web_data=None
        )

    # 🌍 Environment button
    if "help environment" in text or "🌍" in text:

        local_data = local_search(
            category="Environment",
            query="environment cleanup trees ecology"
        )

        return synthesize_answer(
            user_input=user_input,
            local_data=local_data,
            web_data=None
        )

    # 🤝 Community button
    if "help people" in text or "community" in text or "🤝" in text:

        local_data = local_search(
            category="Community",
            query="community homeless elderly refugees"
        )

        return synthesize_answer(
            user_input=user_input,
            local_data=local_data,
            web_data=None
        )

    # 🌱 Suggest random deed
    if "suggest" in text or "good deed" in text:

        local_data = local_search(
            category="mixed",
            query="random"
        )

        return synthesize_answer(
            user_input=user_input,
            local_data=local_data,
            web_data=None
        )

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
        query=" ".join(keywords)
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

    return synthesize_answer(
        user_input=user_input,
        local_data=local_data,
        web_data=web_data
    )