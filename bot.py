from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import ensure_env
from db import init_db, list_all_users
from handlers import (
    cmd_start, cmd_language, on_language_pick,
    cmd_setcity, cmd_addevent, cmd_myevents, cmd_delete, cmd_checktoday,
    cmd_ping, debug_echo, schedule_user_daily_job
)

def main():
    token = ensure_env("TELEGRAM_BOT_TOKEN")
    # OWM_API_KEY is checked lazily inside handlers/weather path

    init_db()

    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("language", cmd_language))
    app.add_handler(CallbackQueryHandler(on_language_pick, pattern=r"^lang:(en|ru)$"))

    app.add_handler(CommandHandler("setcity", cmd_setcity))
    app.add_handler(CommandHandler("addevent", cmd_addevent))
    app.add_handler(CommandHandler("myevents", cmd_myevents))
    app.add_handler(CommandHandler("delete", cmd_delete))
    app.add_handler(CommandHandler("checktoday", cmd_checktoday))

    # Debug
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(MessageHandler(filters.ALL, debug_echo))

    # Recreate daily jobs for all existing users on startup
    async def _post_init(app_):
        for u in list_all_users():
            await schedule_user_daily_job(app_.job_queue, u["user_id"], u["timezone"])
    app.post_init = _post_init

    print("Bot is running (polling). Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
