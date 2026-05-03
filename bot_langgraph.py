import os
from dotenv import load_dotenv

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from langchain_community.chat_models import ChatMistralAI
from langchain_community.tools.tavily_search import TavilySearchResults

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional

# ======================
# INIT
# ======================
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ======================
# STATE
# ======================

class AgentState(TypedDict, total=False):
    messages: List[str]
    context: str
    location: Optional[str]
    action: str
    query: str

# ======================
# TOOLS
# ======================

tavily_tool = TavilySearchResults(max_results=3)

# ======================
# NODES
# ======================

llm = ChatMistralAI(model="mistral-small-latest", temperature=0, api_key=MISTRAL_API_KEY)

def agent_node(state: AgentState):
    user_input = state["messages"][-1]
    user_location = state.get("location", "")

    location_info = f"\nUSER LOCATION:\n{user_location}\n" if user_location else ""
    prompt = f"""
You are an AI agent that helps people do real acts of kindness.

You have access to real-world search results.
{location_info}
USER REQUEST:
{user_input}

REAL DATA:
{state.get("context", "")}

INSTRUCTIONS:
1. Think about what user wants
2. Use real data when possible
3. Suggest 3 practical real-world actions (consider location if given)
4. Keep it simple
5. No markdown

Decide:
- If you need more info → say: SEARCH: query
- If you are ready → give final answer

Answer format:
Either:
SEARCH: ...
or
FINAL: ...
"""

    try:
        response = llm.invoke(prompt).content
    except Exception as e:
        return {
            "messages": state["messages"] + [f"FINAL: {str(e)}"],
            "action": "final",
            "location": state.get("location", "")
        }

    if response.startswith("SEARCH:"):
        return {
            "messages": state["messages"],
            "action": "search",
            "query": response.replace("SEARCH:", "").strip(),
            "location": state.get("location", "")
        }

    return {
        "messages": state["messages"] + [response],
        "action": "final",
        "location": state.get("location", "")
    }

def search_node(state: AgentState):
    query = state["query"]

    try:
        results = tavily_tool.invoke({"query": query}) or {}
        context = "\n".join(r.get("content", "") for r in results.get("results", []))
    except Exception as e:
        context = f"Tavily error: {e}"

    return {
        "messages": state["messages"],
        "context": context,
        "location": state.get("location", "")
    }

# ======================
# GRAPH
# ======================

builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)
builder.add_node("search", search_node)

def should_continue(state):
    return state.get("action")

builder.set_entry_point("agent")

builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "search": "search",
        "final": END
    }
)

builder.add_edge("search", "agent")

graph = builder.compile()

# ======================
# TELEGRAM + GEOLOCATION STATE
# ======================

user_state = {}

GEO_LOC_BUTTONS = [
    [KeyboardButton(text="📍 Поделиться своей локацией", request_location=True)],
    [KeyboardButton(text="🏙️ Указать свою локацию")]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"history": [], "location": None, "waiting_for_location": False}

    reply_markup = ReplyKeyboardMarkup(GEO_LOC_BUTTONS, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "🤖 Be Kind (LangGraph Agent)\n\n"
        "Просто напиши:\n"
        "• help animals\n"
        "• 30 min kindness\n"
        "• volunteer nearby\n\n"
        "Для персонализированных идей укажите свою локацию или поделитесь ею.",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message
    text = message.text if message.text else ""
    entry = user_state.setdefault(user_id, {"history": [], "location": None, "waiting_for_location": False})

    # 1. Process location from user (device location-message)
    if message.location:
        lat, lon = message.location.latitude, message.location.longitude
        entry["location"] = f"{lat},{lon}"
        entry["waiting_for_location"] = False
        await message.reply_text(
            "Спасибо! Ваша локация сохранена. Теперь опишите, какое добро вы хотите сделать.",
            reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True, one_time_keyboard=True)
        )
        return

    # 2. User selects "enter location manually"
    if text.strip() in ["🏙️ Указать свою локацию"]:
        await message.reply_text("Пожалуйста, напишите город, адрес или локацию, где вы находитесь:")
        entry["waiting_for_location"] = True
        return

    # 3. User enters location manually (after selecting manual input)
    if entry.get("waiting_for_location", False):
        entry["location"] = text.strip()
        entry["waiting_for_location"] = False
        await message.reply_text(
            f"Спасибо! Ваша локация сохранена как: {entry['location']}.\nТеперь напишите, какое доброе дело вы хотите совершить.",
            reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True, one_time_keyboard=True)
        )
        return

    # 4. Normal user request
    entry["history"].append(text)
    user_location = entry.get("location", "")

    await message.reply_text("🤔 Thinking...")

    try:
        result = graph.invoke({
            "messages": [text],
            "context": "",
            "location": user_location
        })
        answer = result["messages"][-1]
        # убираем FINAL:
        answer = answer.replace("FINAL:", "").strip()
        await message.reply_text(answer)

    except Exception as e:
        print(e)
        await message.reply_text("Error 😔")

# ======================
# MAIN
# ======================

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("LangGraph bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()