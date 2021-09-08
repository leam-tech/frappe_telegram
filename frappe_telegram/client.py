from telegram.bot import Bot

import frappe
from frappe_telegram.handlers.logging import log_outgoing_message

"""
The functions defined here is provided to invoke the bot
without Updaters & Dispatchers. This is helpful for triggering
bot interactions via Hooks / Controller methods
"""


def send_message(message_text: str, user=None, telegram_user=None, from_bot=None):
    telegram_user_id = get_telegram_user_id(user=user, telegram_user=telegram_user)
    if not from_bot:
        from_bot = frappe.get_value("Telegram Bot", {})

    bot = get_bot(from_bot)
    message = bot.send_message(telegram_user_id, text=message_text)
    log_outgoing_message(telegram_bot=from_bot, result=message)

def send_file(file, filename=None, message=None, user=None, telegram_user=None, from_bot=None):
    '''
    Send a file to the bot

    file: (`str` | `filelike object` | `bytes` | `pathlib.Path` | `telegram.Document`)
        The file can be either a file_id, a URL or a file from disk
    filename: `str`
        Specify custom file name
    message: `str`
        Small text to show alongside the file. 0-1024 characters
    '''

    telegram_user_id = get_telegram_user_id(
        user=user, telegram_user=telegram_user)
    if not from_bot:
        from_bot = frappe.get_value("Telegram Bot", {})

    bot = get_bot(from_bot)
    result = bot.send_document(telegram_user_id, document=file, filename=filename, caption=message)
    log_outgoing_message(telegram_bot=from_bot, result=result)


def get_telegram_user_id(user=None, telegram_user=None):
    if not user and not telegram_user:
        frappe.throw(frappe._("Please specify either frappe-user or telegram-user"))

    telegram_user_id = None
    if user and frappe.db.exists("Telegram User", {"user": user}):
        telegram_user_id = frappe.db.get_value("Telegram User", {"user": user}, "telegram_user_id")

    if telegram_user and not telegram_user_id:
        telegram_user_id = frappe.db.get_value("Telegram User", telegram_user, "telegram_user_id")

    if not telegram_user_id:
        frappe.throw(frappe._("Telegram user do not exist"))

    return telegram_user_id


def get_bot(telegram_bot) -> Bot:
    from telegram.ext import ExtBot
    telegram_bot = frappe.get_doc("Telegram Bot", telegram_bot)

    return ExtBot(
        token=telegram_bot.get_password("api_token")
    )
