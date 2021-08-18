from typing import Union
import frappe
from frappe_telegram import Update, CallbackContext, Message


def logger_handler(update: Update, context: CallbackContext):
    if not hasattr(update, "effective_user"):
        return
    context.telegram_user = get_telegram_user(update)
    context.telegram_chat = get_telegram_chat(update)
    if context.telegram_chat and context.telegram_user:
        context.telegram_message = get_telegram_message(
            update, context.telegram_chat, context.telegram_user)


def log_outgoing_message(telegram_bot: str, result: Union[bool, Message]):
    if not isinstance(result, Message):
        return
    msg = frappe.get_doc(
        doctype="Telegram Message",
        chat=frappe.db.get_value("Telegram Chat", {"chat_id": result.chat_id}),
        message_id=result.message_id,
        content=result.text, from_bot=telegram_bot)
    msg.insert(ignore_permissions=True)


def get_telegram_user(update: Update):
    telegram_user = update.effective_user
    user = frappe.db.get_value("Telegram User", {"telegram_user_id": telegram_user.id})
    if user:
        return frappe.get_cached_doc("Telegram User", user)

    full_name = telegram_user.first_name
    if telegram_user.last_name:
        full_name += " " + telegram_user.last_name

    user = frappe.get_doc(
        doctype="Telegram User",
        telegram_user_id=telegram_user.id,
        telegram_username=telegram_user.username,
        full_name=full_name.strip())
    user.insert(ignore_permissions=True)
    frappe.db.commit()

    return user


def get_telegram_chat(update: Update):
    if not update.effective_chat:
        return

    telegram_chat = update.effective_chat
    chat = frappe.db.get_value("Telegram Chat", {"chat_id": telegram_chat.id})
    if chat:
        chat = frappe.get_cached_doc("Telegram Chat", chat)
    else:
        chat = frappe.get_doc(
            doctype="Telegram Chat", chat_id=telegram_chat.id,
            title=telegram_chat.title or telegram_chat.username or telegram_chat.first_name,
            type=telegram_chat.type, users=[]
        )
        chat.insert(ignore_permissions=True)

    return chat


def get_telegram_message(update: Update, telegram_chat, telegram_user):
    if not update.effective_message:
        return

    telegram_message = update.effective_message
    msg = frappe.get_doc(
        doctype="Telegram Message", chat=telegram_chat.name, message_id=telegram_message.message_id,
        content=telegram_message.text, from_user=telegram_user.name)
    msg.insert(ignore_permissions=True)
