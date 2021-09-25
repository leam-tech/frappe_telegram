import frappe
from frappe.utils.password import check_password
from frappe_telegram import (
    Update,
    CallbackContext,
    Updater, DispatcherHandlerStop,
    InlineKeyboardMarkup, ConversationHandler,
    InlineKeyboardButton)
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.messagehandler import MessageHandler

LOGIN_CONV_ENTER = frappe.generate_hash()
SIGNUP_CONV_ENTER = frappe.generate_hash()

ENTERING_CREDENTIALS = frappe.generate_hash()


def attach_conversation_handler(telegram_bot, updater: Updater):
    from .auth import AUTH_HANDLER_GROUP
    # Login Conversation
    updater.dispatcher.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(
            ask_email, pattern=f"^{LOGIN_CONV_ENTER}$"
        )],
        states={
            ENTERING_CREDENTIALS: [
                MessageHandler(None, collect_email_and_ask_for_pwd), ]
        },
        fallbacks=[],
    ), group=AUTH_HANDLER_GROUP)


def login_handler(update: Update, context: CallbackContext):
    text = "Hi, please authenticate first before you continue"
    buttons = [
        [
            InlineKeyboardButton(text='Login', callback_data=str(LOGIN_CONV_ENTER)),
            InlineKeyboardButton(text='Signup', callback_data=str(SIGNUP_CONV_ENTER)),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    update.effective_message.reply_text(text=text, reply_markup=keyboard)
    raise DispatcherHandlerStop()


def ask_email(update: Update, context: CallbackContext):
    update.effective_message.reply_text("Please enter your Email ID")
    raise DispatcherHandlerStop(state=ENTERING_CREDENTIALS)


def collect_email_and_ask_for_pwd(update: Update, context: CallbackContext):
    if not update.message.text:
        update.effective_message.reply_text("Please enter a valid input")
        return

    if "email" not in context.user_data:
        context.user_data["email"] = update.message.text
        update.message.reply_text("Please enter your password")
        raise DispatcherHandlerStop(state=ENTERING_CREDENTIALS)

    # Delete the incoming password on Client side and Mask it in logs
    context.telegram_message.mark_as_password()
    password = update.message.text

    user = verify_credentials(context.user_data["email"], password)
    if user and user.is_authenticated:
        # Authenticated! Lets link FrappeUser & TelegramUser
        update.message.reply_text("You have successfully logged in as: " + user.name)
        context.telegram_user.db_set("user", user.name)
        frappe.clear_document_cache(context.telegram_user.doctype, context.telegram_user.name)
        raise DispatcherHandlerStop(state=ConversationHandler.END)
    else:
        del context.user_data["email"]
        update.message.reply_text("You have entered invalid credentials. Please try again")
        return ask_email(update, context)


def verify_credentials(email, pwd):
    from frappe.core.doctype.user.user import User

    try:
        user = User.find_by_credentials(email, pwd)
        return user
    except AttributeError:
        users = frappe.db.get_all(
            'User', fields=['name', 'enabled'], or_filters=[{"name": email}], limit=1)
        if not users:
            return

        user = users[0]
        user['is_authenticated'] = True
        try:
            check_password(user['name'], pwd)
        except frappe.AuthenticationError:
            user['is_authenticated'] = False

        return user
