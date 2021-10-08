# Example: Activity Notifier
Get notified when any doc-updates are made

- Add the following to hooks.py of your custom-app
```py
doc_events = {
  "*": {
    "after_insert": "botter.activity_notifier.on_activity",
    "on_update": "botter.activity_notifier.on_activity",
    "on_trash": "botter.activity_notifier.on_activity",
    "on_submit": "botter.activity_notifier.on_activity",
    "on_cancel": "botter.activity_notifier.on_activity",
  }
}
```

- Implement the handler
```py
import frappe
from frappe_telegram.client import send_message


def on_activity(doc, method):
    users = set([
        x.parent for x in frappe.get_all(
            "Has Role", {"role": "System Manager"}, ["parent"])])

    if doc.doctype in ["Telegram Chat", "Telegram Message", "Version", "Comment", "Activity Log"]:
        return

    message_dict = {
        "on_update": "Updated",
        "on_submit": "Submitted",
        "on_cancel": "Cancelled",
        "on_trash": "Deleted",
        "after_insert": "Inserted",
    }

    for user in users:
        if user == frappe.session.user:
            continue

        try:
            send_message(
                message_text=f"{doc.doctype} {doc.name} {message_dict[method]}",
                user=user)
        except Exception:
            frappe.clear_last_message()

```