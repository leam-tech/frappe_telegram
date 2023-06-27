import frappe
from frappe.utils.password import check_password
from frappe_telegram import (
    Update, CallbackContext,
    Updater, DispatcherHandlerStop, CallbackQueryHandler,
    InlineKeyboardMarkup, ConversationHandler, MessageHandler,
    InlineKeyboardButton)
from frappe_telegram.utils.conversation import collect_conversation_details
from frappe.integrations.doctype.ldap_settings.ldap_settings import LDAPSettings

LOGIN_CONV_ENTER = frappe.generate_hash()
SIGNUP_CONV_ENTER = frappe.generate_hash()

ENTERING_LOGIN_CREDENTIALS = frappe.generate_hash()
ENTERING_SIGNUP_DETAILS = frappe.generate_hash()


def attach_conversation_handler(telegram_bot, updater: Updater):
    from . import AUTH_HANDLER_GROUP
    # Login Conversation
    updater.dispatcher.add_handler(ConversationHandler(
        entry_points=[
            CallbackQueryHandler(collect_login_credentials, pattern=f"^{LOGIN_CONV_ENTER}$"),
            CallbackQueryHandler(collect_signup_details, pattern=f"^{SIGNUP_CONV_ENTER}$"),
        ],
        states={
            ENTERING_LOGIN_CREDENTIALS: [
                MessageHandler(None, collect_login_credentials), ],
            ENTERING_SIGNUP_DETAILS: [
                MessageHandler(None, collect_signup_details), ]
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


def collect_login_credentials(update: Update, context: CallbackContext):
    details = collect_conversation_details(
        key="login_details",
        meta=[
            dict(key="email", label="Email", type="regex", options=r"^.+\@.+\..+$"),
            dict(key="pwd", label="Password", type="password"), ],
        update=update,
        context=context,
    )
    if not details.get("_is_complete"):
        raise DispatcherHandlerStop(state=ENTERING_LOGIN_CREDENTIALS)

    user = verify_credentials(details.email, details.pwd)

    if frappe.db.get_value("LDAP Settings", "enabled") and not user.is_authenticated:
        ldap: LDAPSettings = frappe.get_doc("LDAP Settings")
        user = ldap.authenticate(details.email, details.pwd)
        if user: user["is_authenticated"] = True

    if user and user.is_authenticated:
        # Authenticated! Lets link FrappeUser & TelegramUser
        update.message.reply_text("You have successfully logged in as: " + user.name)
        context.telegram_user.db_set("user", user.name)
        raise DispatcherHandlerStop(state=ConversationHandler.END)
    else:
        update.message.reply_text("You have entered invalid credentials. Please try again")
        return collect_login_credentials(update, context)


def collect_signup_details(update: Update, context: CallbackContext):
    details = collect_conversation_details(
        key="signup_details",
        meta=[
            dict(label="First Name", key="first_name", type="str"),
            dict(label="Last Name", key="last_name", type="str"),
            dict(key="email", label="Email", type="regex", options=r"^.+\@.+\..+$"),
            dict(key="pwd", label="Password", type="password"),
            # dict(key="gender", label="Gender", type="select", options="Male\nFemale"),
        ],
        update=update,
        context=context,
    )
    if not details.get("_is_complete"):
        raise DispatcherHandlerStop(state=ENTERING_SIGNUP_DETAILS)

    user = frappe.get_doc(dict(
        doctype="User",
        email=details.email,
        first_name=details.first_name,
        last_name=details.last_name,
        enabled=1,
        new_password=details.pwd,
        send_welcome_email=0,
    ))
    user.flags.telegram_user_signup = True
    user.insert(ignore_permissions=True)

    context.telegram_user.db_set("user", user.name)
    update.effective_chat.send_message(
        frappe._("You have successfully signed up as: {0}").format(
            user.name))

    return ConversationHandler.END


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
