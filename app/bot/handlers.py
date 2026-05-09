from telegram import Update
from telegram.ext import ContextTypes

from app.bot.keyboards import main_keyboard, good_deed_keyboard
from app.agent.workflow import run_workflow


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to BeKind 🌱\nFind real ways to do good in the world.",
        reply_markup=main_keyboard()
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    result = run_workflow(user_text)

    # 🌱 RANDOM GOOD DEEDS
    if isinstance(result, dict) and result.get("type") == "random_deeds":
        items = result["data"]

        context.user_data["last_options"] = items

        text = "Here are 3 ways you can do good today:\n\n"

        for i, item in enumerate(items, 1):
            text += f"{i}. {item['name']}\n{item['description']}\n\n"

        await update.message.reply_text(
            text,
            reply_markup=good_deed_keyboard()
        )
        return

    # ❓ CLARIFICATION
    if isinstance(result, dict) and result.get("type") == "clarification":
        await update.message.reply_text(result["message"])
        return

    # 📦 LIST RESULTS
    if isinstance(result, list):
        if len(result) == 0:
            await update.message.reply_text("No results found.")
            return

        formatted = "\n\n".join(
            [f"{r['name']}\n{r['description']}" for r in result]
        )

        await update.message.reply_text(formatted)
        return

    # 🧠 DEFAULT
    await update.message.reply_text(str(result))


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "more_like_this":
        await query.message.reply_text("🔁 Finding similar opportunities...")

    elif data == "different_category":
        await query.message.reply_text("🌍 Try: animals / environment / community")

    elif data == "done":
        await query.message.reply_text("💚 Thank you for doing good today!")