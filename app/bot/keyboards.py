from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["🌱 Suggest a good deed"],
            ["🐾 Help animals", "🌍 Help environment"],
            ["🤝 Help people / community"],
        ],
        resize_keyboard=True
    )


def good_deed_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔁 More like this", callback_data="more_like_this"),
        ],
        [
            InlineKeyboardButton("🌍 Different category", callback_data="different_category"),
        ],
        [
            InlineKeyboardButton("✅ I will do it", callback_data="done"),
        ]
    ])