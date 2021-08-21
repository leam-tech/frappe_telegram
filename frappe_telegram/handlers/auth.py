import frappe
from frappe_telegram import Update, CallbackContext, Updater, MessageHandler
from .login import login_handler

AUTH_HANDLER_GROUP = -100


def setup(telegram_bot, updater: Updater):
    from .auth import AUTH_HANDLER_GROUP
    updater.dispatcher.add_handler(MessageHandler(None, authenticate), group=AUTH_HANDLER_GROUP)


def authenticate(update: Update, context: CallbackContext):
    frappe.set_user("Guest")
    # if not update.effective_user:
    #     raise DispatcherHandlerStop()

    user = update.effective_user
    telegram_user = frappe.db.get_value("Telegram User", {"telegram_user_id": user.id}, "*")

    if telegram_user and telegram_user.user:
        print("Set-Auth")
        update.effective_message.reply_text("Logged in as " + telegram_user.user)
        frappe.set_user(telegram_user.user)
        return

    if telegram_user and telegram_user.is_guest:
        # Guest Telegram User
        return

    auth_handlers = frappe.get_hooks("telegram_auth_handlers")
    for cmd in reversed(auth_handlers):
        r = frappe.get_attr(cmd)(update=update, context=context)
        if r is not None:
            return r

    login_handler(update=update, context=context)
