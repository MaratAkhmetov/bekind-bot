import traceback

from telegram import Update
from telegram.ext import ContextTypes

from app.bot.keyboards import main_keyboard, after_answer_keyboard
from app.agent.workflow import run_workflow, repeat_last_search  # assuming repeat_last_search exists

WELCOME_TEXT = """Welcome to BeKind 🌱

Find real ways to do good in the world.

Choose an option from the keyboard below, or simply write what kind of good deed you'd like to do."""

def _reset_user_state(context):
    context.user_data.pop("replay", None)
    context.user_data.pop("shown_names", None)

def _update_shown_names(context, new_items):
    # Keep shown_names as set for uniqueness
    prev = set(context.user_data.get("shown_names", []))
    names = {i.get("name") for i in new_items if i.get("name")}
    context.user_data["shown_names"] = prev | names

async def _handle_suggest_another(update, context):
    replay = context.user_data.get("replay")
    exclude = list(context.user_data.get("shown_names", []))
    if not replay:
        await update.message.reply_text(
            "Use the main buttons or describe what you'd like first.",
            reply_markup=main_keyboard(),
        )
        return
    result = repeat_last_search(replay, exclude_names=exclude)
    if isinstance(result, dict) and result.get("type") == "answer":
        items = result.get("items", [])
        if not items and "ничего не найдено" in result.get("text", "").lower():
            await update.message.reply_text(
                "You've seen all suggestions for this search. Try another category or rephrase.",
                reply_markup=after_answer_keyboard()
            )
            return
        await update.message.reply_text(result["text"], reply_markup=after_answer_keyboard())
        context.user_data["replay"] = result["replay"]
        _update_shown_names(context, items)
        return
    else:
        # fallback, should not usually happen
        await update.message.reply_text(
            "No further suggestions found.",
            reply_markup=after_answer_keyboard()
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _reset_user_state(context)
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_text = update.message.text

        print("USER MESSAGE:", user_text)

        # Handle special keyboard button presses (ENGLISH)
        if user_text == "🏠 Main menu":
            _reset_user_state(context)
            await update.message.reply_text(
                "Main menu. What good would you like to do today?",
                reply_markup=main_keyboard()
            )
            return
        elif user_text == "🔁 Suggest another":
            await _handle_suggest_another(update, context)
            return
        elif user_text == "🌍 Change category":
            await update.message.reply_text(
                "Please choose a category: animals / environment / community.",
                reply_markup=main_keyboard()
            )
            return
        elif user_text == "✅ I've picked a good deed":
            await update.message.reply_text(
                "Thank you for choosing to do good! 💚",
                reply_markup=main_keyboard()
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

        # ANSWER TYPE (main result for search)
        if isinstance(result, dict) and result.get("type") == "answer":
            items = result.get("items", [])
            text = result.get("text", "")
            if not items and "ничего не найдено" in text.lower():
                # text indicates nothing found, do not update replay
                await update.message.reply_text(
                    text,
                    reply_markup=after_answer_keyboard()
                )
                return
            await update.message.reply_text(
                text,
                reply_markup=after_answer_keyboard()
            )
            context.user_data["replay"] = result.get("replay")
            _update_shown_names(context, items)
            return

        # 📦 LOCAL RESULTS (legacy, as a list)
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
        # Use the same suggest another logic, but for callback
        replay = context.user_data.get("replay")
        exclude = list(context.user_data.get("shown_names", []))
        if not replay:
            await query.message.reply_text(
                "Use the main buttons or describe what you'd like first.",
                reply_markup=main_keyboard()
            )
            return
        result = repeat_last_search(replay, exclude_names=exclude)
        if isinstance(result, dict) and result.get("type") == "answer":
            items = result.get("items", [])
            if not items and "ничего не найдено" in result.get("text", "").lower():
                await query.message.reply_text(
                    "You've seen all suggestions for this search. Try another category or rephrase.",
                    reply_markup=after_answer_keyboard()
                )
                return
            await query.message.reply_text(result["text"], reply_markup=after_answer_keyboard())
            context.user_data["replay"] = result["replay"]
            _update_shown_names(context, items)
            return
        else:
            await query.message.reply_text(
                "No further suggestions found.",
                reply_markup=after_answer_keyboard()
            )
    elif data == "different_category":
        await query.message.reply_text(
            "🌍 Try: animals / environment / community or write your own idea",
            reply_markup=main_keyboard()
        )

    elif data == "done":
        await query.message.reply_text(
            "💚 Thank you for doing good today!",
            reply_markup=main_keyboard()
        )