from telegram import ReplyKeyboardMarkup

def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["🌱 Suggest a good deed"],
            ["🐾 Help animals", "🌍 Help environment"],
            ["🤝 Help people / community"],
        ],
        resize_keyboard=True
    )

def after_answer_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["🔁 Suggest another"],
            ["🌍 Change category"],
            ["✅ I've picked a good deed"],
        ],
        resize_keyboard=True,
    )