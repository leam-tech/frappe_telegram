import frappe
from frappe.email.doctype.notification.notification import Notification, get_context
from frappe_telegram.client import send_message


"""
Extending Frappe's Notification Channels.
If you would like to extend the list of channels with your own custom channel in your custom app,
Please do not forget to use the module function `send_telegram_notification` to not miss out on
Telegram Notifications.
"""


class TelegramNotification(Notification):
    def send(self, doc):
        if self.channel != "Telegram":
            return super().send(doc)

        return send_telegram_notification(
            notification=self,
            doc=doc,
        )


def send_telegram_notification(notification, doc):
    if notification.channel != "Telegram":
        return

    context = get_context(doc)
    context = {"doc": doc, "alert": notification, "comments": None}
    if doc.get("_comments"):
        context["comments"] = frappe.parse_json(doc.get("_comments"))

    if notification.is_standard:
        notification.load_standard_properties(context)

    users = get_recipients(
        notification=notification, doc=doc, context=context
    )

    message_text = frappe.render_template(notification.message, context)

    for user in users:
        frappe.enqueue(
            method=send_message,
            queue="short",
            message_text=message_text,
            user=user,
            enqueue_after_commit=True
        )


def get_recipients(notification, doc, context):
    recipients = []

    for recipient in notification.recipients:
        if recipient.condition:
            if not frappe.safe_eval(recipient.condition, None, context):
                continue

        if recipient.receiver_by_document_field:
            fields = recipient.receiver_by_document_field.split(',')
            # fields from child table
            if len(fields) > 1:
                for d in doc.get(fields[1]):
                    user = d.get(fields[0])
                    if frappe.db.exists("User", user):
                        recipients.append(user)
            # field from parent doc
            else:
                user = doc.get(fields[0])
                if frappe.db.exists(user):
                    recipients.append(user)

        if recipient.receiver_by_role:
            users = [x.parent for x in frappe.get_all(
                "Has Role",
                filters={"role": recipient.receiver_by_role, "parenttype": "User"},
                fields=["parent"])]
            recipients.extend(users)

    return list(set(recipients))
