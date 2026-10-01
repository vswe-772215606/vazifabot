"""Telegram wiring: handlers, the menu, and the entry point. Runs by long polling, so the
server needs no domain and no open port."""

import logging
import os

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from . import logic, texts
from .storage import TaskStore

log = logging.getLogger("vazifabot")

MENU = ReplyKeyboardMarkup([[texts.BTN_LIST, texts.BTN_HELP]], resize_keyboard=True)


def markup(rows: logic.Rows) -> InlineKeyboardMarkup | None:
    if not rows:
        return None
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data=data) for label, data in row] for row in rows])


def store_of(context: ContextTypes.DEFAULT_TYPE) -> TaskStore:
    return context.bot_data["store"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(texts.START, reply_markup=MENU)


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(texts.HELP, reply_markup=MENU)


async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text, rows = logic.list_view(store_of(context), update.effective_chat.id)
    await update.message.reply_text(text, reply_markup=markup(rows))


async def add_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply = logic.add_from_text(store_of(context), update.effective_chat.id, update.message.text)
    await update.message.reply_text(reply, reply_markup=MENU)


async def not_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(texts.ONLY_TEXT, reply_markup=MENU)


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat_id = update.effective_chat.id
    store = store_of(context)
    await query.answer(logic.handle_button(store, chat_id, query.data or ""))
    text, rows = logic.list_view(store, chat_id)
    try:
        await query.edit_message_text(text, reply_markup=markup(rows))
    except BadRequest as e:
        # a second tap on the same button leaves the list as it was
        if "not modified" not in str(e).lower():
            raise


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("update failed", exc_info=context.error)


async def set_commands(app: Application) -> None:
    await app.bot.set_my_commands([BotCommand(name, about) for name, about in texts.COMMANDS])


def build_app(token: str, db_path: str) -> Application:
    app = Application.builder().token(token).post_init(set_commands).build()
    app.bot_data["store"] = TaskStore(db_path)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["vazifalar", "list"], show_list))
    app.add_handler(CommandHandler(["yordam", "help"], show_help))
    app.add_handler(MessageHandler(filters.Text([texts.BTN_LIST]), show_list))
    app.add_handler(MessageHandler(filters.Text([texts.BTN_HELP]), show_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_tasks))
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & ~filters.TEXT & ~filters.COMMAND & ~filters.StatusUpdate.ALL, not_text))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_error_handler(on_error)
    return app


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    # httpx logs every request URL at INFO, and the URL carries the bot token
    logging.getLogger("httpx").setLevel(logging.WARNING)
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("BOT_TOKEN is not set: copy .env.example to .env and put the token in it.")
    app = build_app(token, os.environ.get("DB_PATH", "data/tasks.db"))
    log.info("vazifabot is running")
    # edited messages are not asked for, so editing a message never adds a task twice
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
