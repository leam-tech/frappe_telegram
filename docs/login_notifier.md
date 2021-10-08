# Example: Login Notifier
Notifies all System Managers when anybody logs into frappe.

- Add `on_login` hook to your custom-app
```python
on_login = "botter.login_notifier.on_login"
```

- Implement the `on_login` handler
```python
import frappe
from frappe_telegram.client import send_message


def on_login(login_manager):
    users = set([
        x.parent for x in frappe.get_all(
            "Has Role", {"role": "System Manager"}, ["parent"])])

    for user in users:
        if user == login_manager.user:
            continue

        try:
            send_message(
                message_text=f"{login_manager.user} logged in",
                user=user)
        except Exception:
            frappe.clear_last_message()

```