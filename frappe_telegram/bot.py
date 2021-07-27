from typing import Union
from telegram.ext import Updater


import frappe
from frappe_telegram.frappe_telegram.doctype import TelegramBot
from telegram.ext.commandhandler import CommandHandler
from telegram.update import Update


def _start(update: Update, context):
    update.message.reply_text("Heylllo")


def start_polling(bot_doc: Union[str, TelegramBot], poll_interval: int = 0):
    updater = get_bot(bot_doc=bot_doc)

    updater.dispatcher.add_handler(CommandHandler("start", _start))

    updater.start_polling(poll_interval=poll_interval)
    updater.idle()


def start_webhook(
        bot_doc: Union[str, TelegramBot],
        listen_host: str = "127.0.0.1",
        webhook_port: int = 80,
        webhook_url: str = None):
    updater = get_bot(bot_doc=bot_doc)
    updater.start_webhook(
        listen=listen_host,
        port=webhook_port,
        webhook_url=webhook_url
    )


def get_bot(bot_doc: Union[str, TelegramBot]) -> Updater:
    if isinstance(bot_doc, str):
        bot_doc = frappe.get_doc("Telegram Bot", bot_doc)

    if frappe.db:
        token = bot_doc.get_password("api_token")
    else:
        token = bot_doc.get("api_token")
    return Updater(token=token)
