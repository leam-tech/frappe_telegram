import frappe


def after_migrate():
    add_telegram_notification_channel()


def add_telegram_notification_channel():
    """
    This will add Telegram to existing list of Channels.
    This will not overwrite other custom channels that came in via custom-apps
    """
    meta = frappe.get_meta('Notification')
    channels = meta.get_field("channel").options.split("\n")
    if "Telegram" in channels:
        return

    channels.append("Telegram")
    frappe.get_doc({
        "doctype": "Property Setter",
        "doctype_or_field": "DocField",
        "doc_type": "Notification",
        "field_name": "channel",
        "property": "options",
        "value": "\n".join(channels),
        "property_type": "Small Text"
    }).insert()
