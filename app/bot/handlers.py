import traceback

from telegram import Update
from telegram.ext import ContextTypes

from app.bot.keyboards import main_keyboard, after_answer_keyboard
from app.agent.workflow import run_workflow


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to BeKind 🌱\nFind real ways to do good in the world.",
        reply_markup=main_keyboard()
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_text = update.message.text

        print("USER MESSAGE:", user_text)

        # Handle special keyboard button presses (ENGLISH)
        if user_text == "🏠 Main menu":
            await update.message.reply_text(
                "Main menu. What good would you like to do today?",
                reply_markup=main_keyboard()
            )
            return
        elif user_text == "🔁 Suggest another":
            await update.message.reply_text(
                "Looking for more options...",
                reply_markup=after_answer_keyboard()
            )
            return
        elif user_text == "🌍 Change category":
            await update.message.reply_text(
                "Please choose a category: animals / environment / community.",
                reply_markup=after_answer_keyboard()
            )
            return
        elif user_text == "✅ I've picked a good deed":
            await update.message.reply_text(
                "Thank you for choosing to do good! 💚",
                reply_markup=after_answer_keyboard()
            )
            return

        result = run_workflow(user_text)

        print("WORKFLOW RESULT:", result)

        # 🌱 RANDOM GOOD DEEDS
        if isinstance(result, dict) and result.get("type") == "random_deeds":
            items = result["data"]
            text = "Here are 3 ways you can do good today:\n\n"
            for i, item in enumerate(items, 1):
                text += f"{i}. {item['name']}\n{item['description']}\n\n"
            await update.message.reply_text(
                text,
                reply_markup=after_answer_keyboard()
            )
            return

        # ❓ CLARIFICATION
        if isinstance(result, dict) and result.get("type") == "clarification":
            await update.message.reply_text(
                result["message"],
                reply_markup=after_answer_keyboard()
            )
            return

        # 📦 LOCAL RESULTS
        if isinstance(result, list):
            if len(result) == 0:
                await update.message.reply_text(
                    "No local results found.",
                    reply_markup=after_answer_keyboard()
                )
                return
            formatted = "\n\n".join(
                [
                    f"{r['name']}\n{r['description']}"
                    for r in result
                ]
            )
            await update.message.reply_text(
                formatted,
                reply_markup=after_answer_keyboard()
            )
            return

        # 🧠 DEFAULT
        await update.message.reply_text(
            str(result),
            reply_markup=after_answer_keyboard()
        )

    except Exception as e:

        print("ERROR:")
        traceback.print_exc()

        await update.message.reply_text(
            "I'm having trouble processing this right now. Try again.",
            reply_markup=after_answer_keyboard()
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "more_like_this":
        await query.message.reply_text(
            "🔁 Finding similar opportunities...",
            reply_markup=after_answer_keyboard()
        )

    elif data == "different_category":
        await query.message.reply_text(
            "🌍 Try: animals / environment / community",
            reply_markup=after_answer_keyboard()
        )

    elif data == "done":
        await query.message.reply_text(
            "💚 Thank you for doing good today!",
            reply_markup=after_answer_keyboard()
        )