import os

from dotenv import load_dotenv
from mistralai.client import MistralClient
from tavily import TavilyClient
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

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

def build_agent_prompt(user_input, context, user_location: str = ""):
    location_info = f"\nUSER LOCATION:\n{user_location}\n" if user_location else ""
    return f"""
You are an AI agent that helps people do real acts of kindness.

You have access to real-world search results.
{location_info}
USER REQUEST:
{user_input}

REAL DATA:
{context}

INSTRUCTIONS:
1. Think about what user wants
2. Use real data when possible
3. Suggest 3 practical real-world actions (consider location if given)
4. Keep it simple
5. No markdown

ANSWER:
"""

# ======================
# HANDLERS
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"history": [], "location": None}

    # Кнопки для выбора или отправки локации
    location_keyboard = [
        [KeyboardButton(text="📍 Поделиться своей локацией", request_location=True)],
        [KeyboardButton(text="🏙️ Указать свою локацию")]
    ]
    reply_markup = ReplyKeyboardMarkup(location_keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "👋 Hi! I'm Be Kind (Agent mode).\n\n"
        "Для персонализированных идей укажите свою локацию или поделитесь ею.\n\n"
        "To get personalized suggestions, please share your location or type your city/address.",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message
    text = message.text if message.text else ""
    user_entry = user_state.setdefault(user_id, {"history": [], "location": None})

    # 1. Обработка геолокации
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        user_entry["location"] = f"{lat},{lon}"
        await message.reply_text(
            f"Спасибо! Ваша локация сохранена. Теперь опишите, какое добро вы хотите сделать. Например:\n"
            "• помочь животным рядом\n"
            "• идеи добрых дел на 30 минут\n"
            "• волонтерство сегодня",
            reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True, one_time_keyboard=True)
        )
        return

    # 2. Пользователь выбирает "Указать свою локацию"
    if text.strip() in ["🏙️ Указать свою локацию"]:
        await message.reply_text("Пожалуйста, напишите город, адрес или локацию, где вы находитесь:")
        user_entry["waiting_for_location"] = True
        return

    if user_entry.get("waiting_for_location", False):
        user_entry["location"] = text.strip()
        user_entry["waiting_for_location"] = False
        await message.reply_text(
            f"Спасибо! Ваша локация сохранена как: {user_entry['location']}.\nТеперь напишите, какое доброе дело вы хотите совершить.",
            reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True, one_time_keyboard=True)
        )
        return

    # 3. Обычный запрос на добрые дела
    user_entry["history"].append(text)

    await message.reply_text("🔎 Ищу возможности рядом с вами...")

    # Формируем поисковый запрос с учетом локации, если она указана
    location_str = user_entry.get("location", "")
    if location_str:
        search_query = f"{text} volunteer help kindness opportunities near {location_str}"
    else:
        search_query = f"{text} volunteer help kindness opportunities near me"

    context_data = search_real_data(search_query)

    await message.reply_text("🤖 Думаю над вашими идеями...")

    try:
        prompt = build_agent_prompt(text, context_data, user_location=location_str)
        response = mistral.chat(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content

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
    # location handler (если пользователь отправил гео)
    app.add_handler(MessageHandler(filters.LOCATION, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Agent bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()