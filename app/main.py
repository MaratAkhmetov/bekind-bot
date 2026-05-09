from telegram.ext import (
    Application,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters
)

from app.config import TELEGRAM_BOT_TOKEN
from app.bot.handlers import handle_message, handle_callback, start

from app.database.db import init_db
from app.database.import_data import import_csv


def main():
   
    init_db()

    import_csv()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", start))

    # messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # callbacks
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("BeKind bot is running... 🌱")
    app.run_polling()


if __name__ == "__main__":
    main()