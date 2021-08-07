from typing import Union
from telegram.ext import Updater


import frappe
from frappe_telegram.frappe_telegram.doctype import TelegramBot
from telegram.ext.commandhandler import CommandHandler
from telegram.update import Update


def _start(update: Update, context):
    update.message.reply_text("Heylllo")


def start_polling(site: str, bot_doc: Union[str, TelegramBot], poll_interval: int = 0):
    updater = get_bot(bot_doc=bot_doc, site=site)

    updater.dispatcher.add_handler(CommandHandler("start", _start))

    updater.start_polling(poll_interval=poll_interval)
    updater.idle()


def start_webhook(
        site: str,
        bot_doc: Union[str, TelegramBot],
        listen_host: str = "127.0.0.1",
        webhook_port: int = 80,
        webhook_url: str = None):
    updater = get_bot(bot_doc=bot_doc, site=site)
    updater.start_webhook(
        listen=listen_host,
        port=webhook_port,
        webhook_url=webhook_url
    )


def get_bot(bot_doc: Union[str, TelegramBot], site=None) -> Updater:
    if not site:
        site = frappe.local.site

    from contextlib import ExitStack
    with frappe.init_site(site) if not frappe.db else ExitStack():
        if not frappe.db:
            frappe.connect()

        if isinstance(bot_doc, str):
            bot_doc = frappe.get_doc("Telegram Bot", bot_doc)

        token = bot_doc.get_password("api_token")

        updater = Updater(token=token)
        handlers = frappe.get_hooks("telegram_bot_handler")
        if isinstance(handlers, dict):
            handlers = handlers[bot_doc.name]

        for cmd in handlers:
            frappe.get_attr(cmd)(botname=bot_doc.name, updater=updater)
