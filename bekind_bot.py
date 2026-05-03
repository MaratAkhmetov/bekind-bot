import os
import random

from dotenv import load_dotenv
from mistralai.client import MistralClient
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Загрузка env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
client = MistralClient(api_key=MISTRAL_API_KEY)

# Хранилище состояния пользователей
user_state = {}

LANG_MAP = {
    "ru": "Russian",
    "en": "English",
    "sr": "Serbian"
}

# Тексты интерфейса
TEXTS = {
    "choose_language": """👋 Hi! I'm Be Kind — your AI guide to real-life kindness.
I help you find simple ways to make someone's day better.

👋 Привет! Я Be Kind — твой помощник в добрых делах.
Помогаю находить простые способы сделать мир чуть лучше.

👋 Zdravo! Ja sam Be Kind — tvoj vodič za dobra dela u stvarnom životu.
Pomažem ti da pronađeš male načine da nekome ulepšaš dan.

🌍 Choose your language / Выбери язык / Izaberi jezik:
""",

    "choose_category": {
        "ru": "Кому или чему сегодня поможем? 👇",
        "en": "Where should we spread some kindness today? 👇",
        "sr": "Kome ili čemu želimo danas da pomognemo? 👇"
    },

    "choose_time": {
        "ru": "Сколько у тебя свободного времени? ⏱",
        "en": "How much free time do you have? ⏱",
        "sr": "Koliko slobodnog vremena imaš? ⏱"
    },

    "loading": {
        "ru": "Уже подбираю подходящие идеи... 🤔",
        "en": "Looking for the best ideas for you... 🤔",
        "sr": "Tražim najbolje ideje za tebe... 🤔"
    },

    "done_msg": {
        "ru": "Это прекрасный выбор! Пусть это маленькое дело сделает мир капельку лучше. ✨",
        "en": "Wonderful choice! May this small act make the world a little brighter. ✨",
        "sr": "Divan izbor! Neka ovo malo delo učini svet bar malo boljim. ✨"
    },

    "main_menu": {
        "ru": "🏠 В главное меню",
        "en": "🏠 Main menu",
        "sr": "🏠 Glavni meni"
    }
}

BACK_TEXT = {"ru": "⬅️ Назад", "en": "⬅️ Back", "sr": "⬅️ Nazad"}
DONE_TEXT = {
    "ru": "✅ Я выбрал доброе дело, спасибо!",
    "en": "✅ I chose an act of kindness, thanks!",
    "sr": "✅ Izabrao sam dobro delo, hvala!"
}

CATEGORY_ROWS = {
    "ru": [["👥 Люди", "🐾 Животные"], ["🌱 Экология", "💬 Общение"]],
    "en": [["👥 People", "🐾 Animals"], ["🌱 Environment", "💬 Social"]],
    "sr": [["👥 Ljudi", "🐾 Životinje"], ["🌱 Ekologija", "💬 Druženje"]]
}

TIME_ROWS = {
    "ru": [["⏱ 15-30 мин", "🕐 1-2 часа"], ["📅 Полдня"]],
    "en": [["⏱ 15-30 min", "🕐 1-2 hours"], ["📅 Half day"]],
    "sr": [["⏱ 15-30 min", "🕐 1-2 sata"], ["📅 Pola dana"]]
}

RESULT_ROWS = {
    "ru": [["🔄 Другие варианты"], ["⚙️ Изменить параметры"]],
    "en": [["🔄 More ideas"], ["⚙️ Change filters"]],
    "sr": [["🔄 Još ideja"], ["⚙️ Promeni parametre"]]
}

def get_kb(rows, lang=None, show_done=False):
    kb_list = [list(row) for row in rows]
    if lang:
        if show_done:
            kb_list = [[DONE_TEXT[lang]]] + kb_list
        kb_list = kb_list + [[BACK_TEXT[lang]]]
    return ReplyKeyboardMarkup(kb_list, resize_keyboard=True)

def build_idea_prompt(lang, category, time):
    target_lang = LANG_MAP.get(lang, "English")
    return f"You MUST answer strictly in {target_lang} language. Suggest 3-5 real-life acts of kindness. Category: {category}. Time: {time}. Be practical. No markdown."

def build_quote_prompt(lang, category):
    target_lang = LANG_MAP.get(lang, "English")
    return f"Provide one short inspirational quote about kindness in {target_lang} language. Context: {category}. Quote and author only. No markdown."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"step": "choose_language"}
    lang_kb = ReplyKeyboardMarkup([["🇷🇺 Русский", "🇬🇧 English"], ["🇷🇸 Srpski"]], resize_keyboard=True)
    await update.message.reply_text(TEXTS["choose_language"], reply_markup=lang_kb)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_state:
        user_state[user_id] = {"step": "choose_language"}
    
    state = user_state[user_id]
    lang = state.get("lang", "en")

    if any(text == DONE_TEXT[l] for l in DONE_TEXT):
        try:
            quote_prompt = build_quote_prompt(lang, state.get("category", "kindness"))
            response = client.chat(model="mistral-small-latest", messages=[{"role": "user", "content": quote_prompt}])
            final_quote = response.choices[0].message.content.replace("**", "").replace("*", "")
            heart_emoji = random.choice(["❤️", "☀️", "🌈", "🕊️", "✨"])
            menu_kb = ReplyKeyboardMarkup([[TEXTS["main_menu"][lang]]], resize_keyboard=True)
            await update.message.reply_text(f"{TEXTS['done_msg'][lang]}\n\n{final_quote}\n\n{heart_emoji}", reply_markup=menu_kb)
            state["step"] = "finished"
        except Exception:
            menu_kb = ReplyKeyboardMarkup([[TEXTS["main_menu"][lang]]], resize_keyboard=True)
            await update.message.reply_text("❤️", reply_markup=menu_kb)
            state["step"] = "finished"
        return

    if any(text == TEXTS["main_menu"][l] for l in TEXTS["main_menu"]):
        state["step"] = "choose_language"
        lang_kb = ReplyKeyboardMarkup([["🇷🇺 Русский", "🇬🇧 English"], ["🇷🇸 Srpski"]], resize_keyboard=True)
        await update.message.reply_text(TEXTS["choose_language"], reply_markup=lang_kb)
        return

    if any(text == BACK_TEXT[l] for l in BACK_TEXT):
        if state["step"] == "choose_category":
            state["step"] = "choose_language"
            lang_kb = ReplyKeyboardMarkup([["🇷🇺 Русский", "🇬🇧 English"], ["🇷🇸 Srpski"]], resize_keyboard=True)
            await update.message.reply_text(TEXTS["choose_language"], reply_markup=lang_kb)
        elif state["step"] == "choose_time":
            state["step"] = "choose_category"
            await update.message.reply_text(TEXTS["choose_category"][lang], reply_markup=get_kb(CATEGORY_ROWS[lang], lang))
        elif state["step"] == "result":
            state["step"] = "choose_time"
            await update.message.reply_text(TEXTS["choose_time"][lang], reply_markup=get_kb(TIME_ROWS[lang], lang))
        return

    if state["step"] == "choose_language":
        if "Русский" in text: lang = "ru"
        elif "English" in text: lang = "en"
        elif "Srpski" in text: lang = "sr"
        else: return
        state.update({"lang": lang, "step": "choose_category"})
        await update.message.reply_text(TEXTS["choose_category"][lang], reply_markup=get_kb(CATEGORY_ROWS[lang], lang))

    elif state["step"] == "choose_category":
        state.update({"category": text, "step": "choose_time"})
        await update.message.reply_text(TEXTS["choose_time"][lang], reply_markup=get_kb(TIME_ROWS[lang], lang))

    elif state["step"] == "choose_time" or (state["step"] == "result" and "🔄" in text):
        if "🔄" not in text: state["time"] = text
        await update.message.reply_text(TEXTS["loading"][lang])
        try:
            prompt = build_idea_prompt(lang, state["category"], state["time"])
            response = client.chat(model="mistral-small-latest", messages=[{"role": "user", "content": prompt}])
            state["step"] = "result"
            clean_answer = response.choices[0].message.content.replace("**", "").replace("*", "")
            await update.message.reply_text(clean_answer)
            await update.message.reply_text("✨", reply_markup=get_kb(RESULT_ROWS[lang], lang, show_done=True))
        except Exception:
            await update.message.reply_text("Error 😔")

    elif state["step"] == "result" and any(x in text for x in ["⚙️", "Promeni", "Change", "Изменить"]):
        state["step"] = "choose_category"
        await update.message.reply_text(TEXTS["choose_category"][lang], reply_markup=get_kb(CATEGORY_ROWS[lang], lang))

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
