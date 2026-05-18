import traceback

from telegram import Update
from telegram.ext import ContextTypes

from app.bot.keyboards import main_keyboard, after_answer_keyboard
from app.agent.workflow import run_workflow, repeat_last_search

from app.agent.memory import (
    save_message,
    build_context_text,
)

WELCOME_TEXT = """Welcome to BeKind 🌱

Find real ways to do good in the world.

Choose an option from the keyboard below, or simply write what kind of good deed you'd like to do."""


def _reset_user_state(context):
    context.user_data.pop("replay", None)
    context.user_data.pop("shown_names", None)
    context.user_data.pop("shown_web_urls", None)


def _update_shown_names(context, new_items):
    prev = set(context.user_data.get("shown_names", []))
    names = {i.get("name") for i in new_items if i and i.get("name")}
    context.user_data["shown_names"] = prev | names


def _update_shown_web_urls(context, new_items):
    prev = set(context.user_data.get("shown_web_urls", []))
    for it in new_items:
        if not isinstance(it, dict):
            continue
        if it.get("_source") != "web":
            continue
        u = it.get("website")
        if u:
            prev.add(str(u).strip().lower().rstrip("/"))
    context.user_data["shown_web_urls"] = prev


def _empty_answer_message(text: str) -> bool:
    t = (text or "").lower()
    return (
        "no initiatives found" in t
        or "ничего не найдено" in t
    )


async def _handle_suggest_another(update, context):
    replay = context.user_data.get("replay")
    exclude = list(context.user_data.get("shown_names", []))
    exclude_urls = list(context.user_data.get("shown_web_urls", []))

    if not replay:
        await update.message.reply_text(
            "Use the main buttons or describe what you'd like first.",
            reply_markup=main_keyboard(),
        )
        return

    result = repeat_last_search(
        replay,
        exclude_names=exclude,
        exclude_urls=exclude_urls
    )

    if isinstance(result, dict) and result.get("type") == "answer":

        items = result.get("items", [])
        text = result.get("text", "")

        if not items or _empty_answer_message(text):
            await update.message.reply_text(
                "You've seen all suggestions we have for this topic. "
                "Try another category or rephrase — or check your web search API key.",
                reply_markup=after_answer_keyboard(),
            )
            return

        await update.message.reply_text(
            result["text"],
            reply_markup=after_answer_keyboard()
        )

        context.user_data["replay"] = result["replay"]

        _update_shown_names(context, items)
        _update_shown_web_urls(context, items)

        return

    await update.message.reply_text(
        "No further suggestions found.",
        reply_markup=after_answer_keyboard(),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    _reset_user_state(context)

    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=main_keyboard(),
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        user_text = update.message.text

        user_id = str(update.effective_user.id)

        context_text = build_context_text(user_id)

        if context_text:
            user_text = f"""
Previous conversation:
{context_text}

Current user message:
{user_text}
"""

        print("USER MESSAGE:", user_text)

        if update.message.text == "🏠 Main menu":

            _reset_user_state(context)

            await update.message.reply_text(
                "Main menu. What good would you like to do today?",
                reply_markup=main_keyboard(),
            )

            return

        if update.message.text == "🔁 Suggest another":

            await _handle_suggest_another(update, context)

            return

        if update.message.text == "🌍 Change category":

            await update.message.reply_text(
                "Please choose a category: animals / environment / community.",
                reply_markup=main_keyboard(),
            )

            return

        if update.message.text == "✅ I've picked a good deed":

            context.user_data.pop("shown_names", None)
            context.user_data.pop("shown_web_urls", None)

            await update.message.reply_text(
                "Thank you for choosing to do good! 💚",
                reply_markup=main_keyboard(),
            )

            return

        # Новый запрос — чистый пул для «Suggest another» по этой теме
        context.user_data.pop("shown_names", None)
        context.user_data.pop("shown_web_urls", None)

        result = run_workflow(
            user_text,
            exclude_urls=list(context.user_data.get("shown_web_urls", [])),
        )

        save_message(
            user_id,
            "user",
            update.message.text
        )

        print("WORKFLOW RESULT:", result)

        if isinstance(result, dict) and result.get("type") == "random_deeds":

            items = result["data"]

            text = "Here are 3 ways you can do good today:\n\n"

            for i, item in enumerate(items, 1):
                text += f"{i}. {item['name']}\n{item['description']}\n\n"

            await update.message.reply_text(
                text,
                reply_markup=after_answer_keyboard(),
            )

            return

        if isinstance(result, dict) and result.get("type") == "clarification":

            await update.message.reply_text(
                result["message"],
                reply_markup=main_keyboard(),
            )

            return

        if isinstance(result, dict) and result.get("type") == "answer":

            items = result.get("items", [])
            text = result.get("text", "")

            if not items or _empty_answer_message(text):

                await update.message.reply_text(
                    text or "No initiatives found.",
                    reply_markup=after_answer_keyboard(),
                )

                return

            save_message(
                user_id,
                "assistant",
                text
            )

            await update.message.reply_text(
                text,
                reply_markup=after_answer_keyboard(),
            )

            context.user_data["replay"] = result.get("replay")

            _update_shown_names(context, items)
            _update_shown_web_urls(context, items)

            return

        if isinstance(result, list):

            if len(result) == 0:

                await update.message.reply_text(
                    "No local results found.",
                    reply_markup=after_answer_keyboard(),
                )

                return

            formatted = "\n\n".join(
                f"{r['name']}\n{r['description']}"
                for r in result
            )

            await update.message.reply_text(
                formatted,
                reply_markup=after_answer_keyboard(),
            )

            return

        await update.message.reply_text(
            str(result),
            reply_markup=after_answer_keyboard(),
        )

    except Exception:

        print("ERROR:")
        traceback.print_exc()

        await update.message.reply_text(
            "I'm having trouble processing this right now. Try again.",
            reply_markup=after_answer_keyboard(),
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = query.data

    if data == "more_like_this":

        replay = context.user_data.get("replay")

        exclude = list(context.user_data.get("shown_names", []))
        exclude_urls = list(context.user_data.get("shown_web_urls", []))

        if not replay:

            await query.message.reply_text(
                "Use the main buttons or describe what you'd like first.",
                reply_markup=main_keyboard(),
            )

            return

        result = repeat_last_search(
            replay,
            exclude_names=exclude,
            exclude_urls=exclude_urls
        )

        if isinstance(result, dict) and result.get("type") == "answer":

            items = result.get("items", [])
            text = result.get("text", "")

            if not items or _empty_answer_message(text):

                await query.message.reply_text(
                    "You've seen all suggestions we have for this topic. "
                    "Try another category or rephrase.",
                    reply_markup=after_answer_keyboard(),
                )

                return

            await query.message.reply_text(
                result["text"],
                reply_markup=after_answer_keyboard()
            )

            context.user_data["replay"] = result["replay"]

            _update_shown_names(context, items)
            _update_shown_web_urls(context, items)

            return

        await query.message.reply_text(
            "No further suggestions found.",
            reply_markup=after_answer_keyboard(),
        )

    elif data == "different_category":

        await query.message.reply_text(
            "🌍 Try: animals / environment / community or write your own idea",
            reply_markup=main_keyboard(),
        )

    elif data == "done":

        await query.message.reply_text(
            "💚 Thank you for doing good today!",
            reply_markup=main_keyboard(),
        )