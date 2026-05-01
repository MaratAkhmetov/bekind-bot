import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from mistralai.client import MistralClient
from tavily import TavilyClient

# ======================
# INIT
# ======================
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

mistral = MistralClient(api_key=MISTRAL_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

user_state = {}

# ======================
# AGENT LOGIC
# ======================

def search_real_data(query: str):
    try:
        result = tavily.search(query=query, max_results=3)
        texts = [r["content"] for r in result["results"]]
        return "\n".join(texts)
    except Exception as e:
        print("Tavily error:", e)
        return ""

def build_agent_prompt(user_input, context):
    return f"""
You are an AI agent that helps people do real acts of kindness.

You have access to real-world search results.

USER REQUEST:
{user_input}

REAL DATA:
{context}

INSTRUCTIONS:
1. Think about what user wants
2. Use real data when possible
3. Suggest 3 practical real-world actions
4. Keep it simple
5. No markdown

ANSWER:
"""

# ======================
# HANDLERS
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"history": []}

    await update.message.reply_text(
        "👋 Hi! I'm Be Kind (Agent mode).\n\n"
        "Just tell me what kind of good you want to do.\n"
        "Example:\n"
        "• help animals nearby\n"
        "• 30 minutes kindness ideas\n"
        "• volunteer today"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_state:
        user_state[user_id] = {"history": []}

    state = user_state[user_id]
    state["history"].append(text)

    await update.message.reply_text("🔎 Searching real opportunities...")

    # 1. SEARCH (tool)
    search_query = f"{text} volunteer help kindness opportunities near me"
    context_data = search_real_data(search_query)

    await update.message.reply_text("🤖 Thinking...")

    # 2. REASON + ANSWER
    try:
        prompt = build_agent_prompt(text, context_data)

        response = mistral.chat(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content

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

    print("Agent bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()