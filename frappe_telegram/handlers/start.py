import frappe
from frappe_telegram import (Updater, Update, CallbackContext, CommandHandler)


def setup(telegram_bot, updater: Updater):
    updater.dispatcher.add_handler(CommandHandler("start", start_handler))


def start_handler(update: Update, context: CallbackContext):
    if frappe.get_hooks("telegram_start_handler"):
        return frappe.get_attr(frappe.get_hooks("telegram_start_handler")[-1])(
            update=update, context=context
        )

    if frappe.session.user == "Guest":
        # Auth Handler will have kicked in and will not reach here
        return

    update.effective_chat.send_message(frappe._("Welcome!"))
    update.effective_chat.send_message(
        frappe._("You are logged in as: {0}").format(
            frappe.db.get_value("User", frappe.session.user, "first_name")))
