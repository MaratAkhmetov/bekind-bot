import os
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

from langgraph.graph import StateGraph, END
from typing import TypedDict, List

# ======================
# INIT
# ======================
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN_3")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ⚠️ ВАЖНО: LangChain ожидает OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = MISTRAL_API_KEY

# ======================
# STATE
# ======================

class AgentState(TypedDict):
    messages: List[str]
    context: str

# ======================
# TOOLS
# ======================

tavily_tool = TavilySearchResults(max_results=3)

# ======================
# NODES
# ======================

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def agent_node(state: AgentState):
    user_input = state["messages"][-1]

    prompt = f"""
You are an AI agent that helps people do real acts of kindness.

User request:
{user_input}

Context:
{state.get("context", "")}

Decide:
- If you need more info → say: SEARCH: query
- If you are ready → give final answer

Answer format:
Either:
SEARCH: ...
or
FINAL: ...
"""

    response = llm.invoke(prompt).content

    if response.startswith("SEARCH:"):
        return {
            "messages": state["messages"],
            "action": "search",
            "query": response.replace("SEARCH:", "").strip()
        }

    return {
        "messages": state["messages"] + [response],
        "action": "final"
    }

def search_node(state: dict):
    query = state["query"]

    results = tavily_tool.invoke({"query": query})

    context = "\n".join([r["content"] for r in results])

    return {
        "messages": state["messages"],
        "context": context
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
# TELEGRAM
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Be Kind (LangGraph Agent)\n\n"
        "Просто напиши:\n"
        "• help animals\n"
        "• 30 min kindness\n"
        "• volunteer nearby"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    await update.message.reply_text("🤔 Thinking...")

    try:
        result = graph.invoke({
            "messages": [text],
            "context": ""
        })

        answer = result["messages"][-1]

        # убираем FINAL:
        answer = answer.replace("FINAL:", "").strip()

        await update.message.reply_text(answer)

    except Exception as e:
        print(e)
        await update.message.reply_text("Error 😔")

# ======================
# MAIN
# ======================

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("LangGraph bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()