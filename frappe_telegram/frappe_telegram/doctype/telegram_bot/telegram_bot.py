# Copyright (c) 2021, Leam Technology Systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe_telegram.frappe_telegram.doctype.telegram_bot import DEFAULT_TELEGRAM_BOT_KEY


class TelegramBot(Document):
    def autoname(self):
        self.name = self.title.replace(" ", "-")

    def validate(self):
        self.set_nginx_path()

    def after_insert(self):
        default_bot = frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY)
        if not default_bot:
            frappe.db.set_default(DEFAULT_TELEGRAM_BOT_KEY, self.title)

    def after_delete(self):
        default_bot = frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY)
        if default_bot == self.title:
            frappe.db.set_default(DEFAULT_TELEGRAM_BOT_KEY, frappe.get_value("Telegram Bot", {}))

    def set_nginx_path(self):
        if self.webhook_nginx_path:
            return

        if not self.webhook_url:
            return

        self.webhook_nginx_path = "/" + self.webhook_url.rstrip("/").split("/")[-1]

    @frappe.whitelist()
    def mark_as_default(self):
        frappe.db.set_default(DEFAULT_TELEGRAM_BOT_KEY, self.name)
        frappe.msgprint(frappe._(f"Set {self.get('title')} as the default bot for notifications."))
