import frappe
from frappe_telegram.handlers.logging import log_outgoing_message


def send_message(message_text: str, user=None, telegram_user=None, from_bot=None):
    telegram_user_id = get_telegram_user_id(user=user, telegram_user=telegram_user)
    if not from_bot:
        from_bot = frappe.get_value("Telegram Bot", {})

    bot = get_bot(from_bot)
    message = bot.send_message(telegram_user_id, text=message_text)
    log_outgoing_message(telegram_bot=from_bot, result=message)


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


def get_bot(telegram_bot):
    from telegram.ext import ExtBot
    telegram_bot = frappe.get_doc("Telegram Bot", telegram_bot)

    return ExtBot(
        token=telegram_bot.get_password("api_token")
    )
