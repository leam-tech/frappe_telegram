import frappe


@frappe.whitelist()
def get_telegram_chat(chat_type, user=None, group=None):
    chat_type = chat_type.lower()
    if chat_type == "private":
        telegram_user_id = frappe.db.get_value("Telegram User", {"user": user}, "telegram_user_id")
        if not telegram_user_id:
            frappe.throw(frappe._("No TelegramUser account exists for user: {0}").format(user))

        # Chat ID == Telegram User ID for private chats
        return telegram_user_id
    elif chat_type == "group":
        if not frappe.db.exists("Telegram Chat", group):
            frappe.throw(frappe._("Unknown Chat: {0}").format(group))

        return group
    else:
        frappe.throw(frappe._("Unknown chat type"))


@frappe.whitelist()
def load_chat_rooms(limit_start, limit_page_length):
    return frappe.db.sql(
        f"""
        SELECT
            chat_id, title, type, last_message_on, last_message_content
        FROM `tabTelegram Chat`
        ORDER BY last_message_on DESC
        LIMIT {limit_start}, {limit_page_length}
        """,
        as_dict=1
    )


@frappe.whitelist()
def load_chat_messages(chat_id, limit_start, limit_page_length):
    return reversed(frappe.db.sql(
        f"""
            SELECT
                name, content, from_user, from_bot, message_id, creation
            FROM `tabTelegram Message`
            WHERE chat=%(chat)s
            ORDER BY modified DESC
            LIMIT {limit_start}, {limit_page_length}
        """,
        {"chat": chat_id},
        as_dict=1
    ))
