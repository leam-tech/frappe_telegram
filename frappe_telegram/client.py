import os
import frappe
from frappe import _
from frappe.core.doctype.file.file import File
from frappe.utils.jinja import render_template
from frappe_telegram import Bot, ParseMode
from frappe_telegram.utils.formatting import strip_unsupported_html_tags
from frappe_telegram.frappe_telegram.doctype.telegram_bot import DEFAULT_TELEGRAM_BOT_KEY
from frappe_telegram.handlers.logging import log_outgoing_message

"""
The functions defined here is provided to invoke the bot
without Updaters & Dispatchers. This is helpful for triggering
bot interactions via Hooks / Controller methods
"""


def send_message(message_text: str, parse_mode=None, user=None, telegram_user=None, from_bot=None):
    """
    Send a message using a bot to a Telegram User

    message_text: `str`
        A text string between 0 and 4096 characters that will be the message
    parse_mode: `ParseMode`
        Choose styling for your message using a ParseMode class constant. Default is `None`
    user: `str`
        Can optionally be used to resolve `telegram_user` using a User linked to a Telegram User
    telegram_user: `str`
        Selects the Telegram User to send the message to. Can be skipped if `user` is set
    from_bot: `str`
        Explicitly specify a bot name to send message from; the default is used if none specified
    """

    message_text = sanitize_message_text(message_text, parse_mode)

    telegram_user_id = get_telegram_user_id(user=user, telegram_user=telegram_user)
    if not from_bot:
        from_bot = frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY)

    bot = get_bot(from_bot)
    message = bot.send_message(telegram_user_id, text=message_text, parse_mode=parse_mode)
    log_outgoing_message(telegram_bot=from_bot, result=message)


def send_file(file, filename=None, message=None, parse_mode=None, user=None, telegram_user=None,
              from_bot=None):
    """
    Send a file to the bot

    file: (`str` | `filelike object` | `bytes` | `pathlib.Path` | `telegram.Document` | `frappe.File`)
        The file can be an internal file path, a telegram file_id, a URL, a File doc or a file from disk.
            internal file path examples: "/files/example.png", "/private/files/example.png"
    filename: `str`
        Specify custom file name
    message: `str`
        Small text to show alongside the file. 0-1024 characters
    parse_mode: `ParseMode`
        Choose styling for your message using a ParseMode class constant. Default is `None`
    """

    message = sanitize_message_text(message, parse_mode)

    telegram_user_id = get_telegram_user_id(
        user=user, telegram_user=telegram_user)
    if not from_bot:
        from_bot = frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY)

    if isinstance(file, File):
        file = file.file_url

    if isinstance(file, str) and "/files/" in file:

        # If file is string, check that the url is internal

        file_path = frappe.get_site_path(
            (("" if "/private/" in file else "/public") + file).strip("/"))

        if os.path.exists(file_path):
            file = open(file_path, 'rb')

    bot = get_bot(from_bot)
    result = bot.send_document(telegram_user_id, document=file, filename=filename, caption=message,
                               parse_mode=parse_mode)
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


@frappe.whitelist()
def send_message_from_template(template: str, context: dict = None, lang: str = None,
                               parse_mode=None, user=None, telegram_user=None, from_bot=None):
    """
    Use a Telegram Message Template to send a message

    template: `str`
        Name of a Telegram Message Template
    context: `dict`
        dict of key:values to resolve the tags in the template
    lang: `str`
        Optionally can be set if an alternative template language is needed
    """

    message = render_message_from_template(template, context=context, lang=lang)

    send_message(message, parse_mode, user, telegram_user, from_bot)


def render_message_from_template(template: str, context: dict = None, lang: str = None) -> str:
    """
    Use a Telegram Message Template to render a message

    template: `str`
        Name of a Telegram Message Template
    context: `dict`
        dict of key:values to resolve the tags in the template
    lang: `str`
        Optionally can be set if an alternative template language is needed
    """
    dt = "Telegram Message Template"

    templates = frappe.get_all(
        dt,
        filters=[{"name": template}]
    )

    if not templates:
        frappe.throw(_("No template with name '{0}' exists.").format(template))

    template_doc = frappe.get_doc(dt, templates[0].name)

    if not context:
        context = {}

    template = ""

    if lang:
        for translation in template_doc.template_translations:
            if translation.language == lang:
                template = translation.template

    if not template:
        template = template_doc.default_template

    return render_template(template, context)


def validate_parse_mode(parse_mode: ParseMode) -> None:
    """
    Validate the parse_mode is a valid ParseMode class constant

    parse_mode: `ParseMode`

    Raises `ValueError` if the parse_mode is not valid
    """
    if parse_mode and parse_mode not in [value for name, value in vars(ParseMode).items() if
                                         not name.startswith('_')]:
        raise ValueError("Please use a valid ParseMode constant.")


def sanitize_message_text(message_text: str, parse_mode: ParseMode = None) -> str:
    """
    Sanitize the message text depending on the parse_mode

    message_text: `str`
        The message text to sanitize

    parse_mode: `ParseMode`
        The parse_mode to use for sanitizing

    Returns `str`
    """
    validate_parse_mode(parse_mode)

    if not parse_mode:
        return message_text

    if parse_mode == ParseMode.HTML:
        # Telegram API throws error if not formatted properly
        return strip_unsupported_html_tags(message_text)

    return message_text
