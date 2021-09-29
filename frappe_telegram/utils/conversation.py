import re
from telegram import ReplyKeyboardMarkup, KeyboardButton

import frappe
from frappe_telegram import Update, CallbackContext


def collect_conversation_details(key, meta, update: Update, context: CallbackContext):
    """
    A conversation-utility function to collect a set of details that
    conform to specific validations

    Meta [
        { key: "email", label: "Email", type: "email", reqd: True },
        { key: "pwd", label: "Password", type: "password", prompt: "Please provide your password" },
        { key: "mobile_no", type: "mobile_no" },
        { key: "num_cars", type: "int" | "integer" },
        { key: "num_kg", type: "flt" | "float" },
        { key: "gender", type: "select", options: "Male\nFemale", reqd: False },
        { key: "custom-id", type: "regex", options: r"^[0-6]{5,8}$" }
    ]

    Supported Meta Types:
    - str | string
    - password (automatically masks the user input)
    - int | integer
    - flt | float
    - select (provide options delimited by \n)
    - regex

    > All details are assumed to be reqd unless explicitly stated as optional
    > You can specify a prompt for the user to enter the value

    Args:
        key: A unique name for the set of details being collected
        meta: A list of individual detail to collect.
        update: Current TelegramUpdate
        context: Current TelegramContext

    Returns:
        An object with collected details and key _is_complete=1 to determine completion
    """

    # Initialize
    if key not in context.user_data:
        context.user_data[key] = frappe._dict(
            _is_complete=False,
            _last_detail_asked=None,
            _next_detail_to_ask=meta[0].get("key"),
        )

    meta_order = [None] + [m.get("key") for m in meta] + [None]
    meta_dict = {
        m.get("key"): frappe._dict(m).update(dict(
            _next_detail_to_ask=meta_order[meta_order.index(m.get("key")) + 1]))
        for m in meta}
    details = context.user_data[key]

    if details._is_complete:
        return details

    # Collect
    if details._last_detail_asked:
        detail_meta = meta_dict[details._last_detail_asked]

        validation_info = _validate_conversation_detail(detail_meta, update, context)
        if not validation_info.validated:
            update.effective_chat.send_message(validation_info.err_message)
            update.effective_chat.send_message(frappe._("Please try again"))
            return details

        details[detail_meta.key] = validation_info.value
        details._next_detail_to_ask = detail_meta._next_detail_to_ask
        if not details._next_detail_to_ask:
            details._is_complete = True

    if details._next_detail_to_ask:
        detail_meta = meta_dict[details._next_detail_to_ask]
        prompt = detail_meta.get("prompt") or "Please provide your {}".format(detail_meta.label)
        reply_markup = None

        if detail_meta.type == "select":
            buttons = []
            # Custom Keyboards are better than Inline-Keyboards in this scenario
            for option in detail_meta.options.split("\n"):
                buttons.append(KeyboardButton(option))
            reply_markup = ReplyKeyboardMarkup([buttons], one_time_keyboard=True)

        update.effective_chat.send_message(frappe._(prompt), reply_markup=reply_markup)

        details._last_detail_asked = details._next_detail_to_ask
        details._next_detail_to_ask = None

    # Return
    if details._is_complete:
        # The handler should carry this information safely from now on
        del context.user_data[key]

    return details


def _validate_conversation_detail(detail_meta, update, context):
    info = frappe._dict(
        validated=True,
        value=None,
        err_message=None,
    )

    # Check select
    if detail_meta.type == "select":
        options = detail_meta.options.split("\n")
        if update.message.text not in options:
            info.err_message = frappe._("Please select from the given options")
            return info.update(dict(validated=False))

        return info.update(dict(value=str(update.message.text)))

    # Check reqd
    if not update.message.text and detail_meta.reqd and detail_meta.type != "select":
        info.err_message = frappe._("This is a required field")
        return info.update(dict(validated=False))

    # The types left all come under update.message.text
    if not update.message.text:
        return info.update(dict(validated=True))

    text = update.message.text
    # Check str | string
    if detail_meta.type in ["str", "string"]:
        return info.update(dict(value=str(text)))
    # Check int | integer
    elif detail_meta.type in ["int", "integer"]:
        try:
            return info.update(dict(value=int(text)))
        except ValueError:
            info.err_message = frappe._("Please enter a valid integer")
            return info.update(dict(validated=False))
    # Check flt | float
    elif detail_meta.type in ["flt", "float"]:
        try:
            return info.update(dict(value=float(text)))
        except ValueError:
            info.err_message = frappe._("Please enter a valid float")
            return info.update(dict(validated=False))
    # Check regex
    elif detail_meta.type == "regex":
        if re.match(detail_meta.options, text):
            return info.update(dict(value=text))
        else:
            info.err_message = frappe._("Please enter a valid {}").format(detail_meta.label)
            return info.update(dict(validated=False))
    # Check Password
    elif detail_meta.type == "password":
        context.telegram_message.mark_as_password()
        return info.update(dict(value=text))
    else:
        info.err_message = frappe._("Invalid type")

    return info.update(dict(validated=False))
