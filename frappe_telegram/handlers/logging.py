import frappe
from frappe_telegram import Update, CallbackContext


def logger_handler(update: Update, context: CallbackContext):
    if not hasattr(update, "effective_user"):
        return
    context.telegram_user = get_telegram_user(update)


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
