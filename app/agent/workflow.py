from app.agent.nodes.intent import analyze_intent
from app.agent.nodes.clarify import ask_clarification
from app.agent.nodes.local_search import local_search
from app.agent.nodes.web_search import web_search
from app.agent.nodes.synthesis import synthesize_answer
from app.database.search import random_initiatives


def run_workflow(user_input: str):

    text = user_input.lower()

    # 🌱 ENTRY: random suggestion
    if "suggest" in text or "good deed" in text:
        data = random_initiatives(limit=3)

        return {
            "type": "random_deeds",
            "data": data
        }

    # 1. INTENT
    intent = analyze_intent(user_input)

    # 2. CLARIFICATION
    if intent.get("needs_clarification"):
        return ask_clarification(intent)

    # 3. LOCAL SEARCH
    category = intent.get("category")
    keywords = intent.get("keywords", [])

    local_data = local_search(
        category=category,
        query=" ".join(keywords)
    )

    # 4. FALLBACK WEB
    if local_data and len(local_data) > 0:
        web_data = None
    else:
        web_data = web_search(user_input)

    # 5. FINAL ANSWER
    return synthesize_answer(
        user_input=user_input,
        local_data=local_data,
        web_data=web_data
    )