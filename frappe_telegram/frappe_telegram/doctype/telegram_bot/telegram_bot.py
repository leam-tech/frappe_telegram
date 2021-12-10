# Copyright (c) 2021, Leam Technology Systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe_telegram.frappe_telegram.doctype.telegram_bot import DEFAULT_TELEGRAM_BOT_KEY


class TelegramBot(Document):
    def autoname(self):
        self.name = self.title.replace(" ", "-")

    def validate(self):
        self.validate_api_token()
        self.set_nginx_path()

    def after_insert(self):
        default_bot = frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY)
        if not default_bot:
            self.mark_as_default()

    def after_delete(self):
        default_bot = frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY)

        if default_bot == self.name:
            new_default_bot = frappe.get_value("Telegram Bot", {})
            frappe.db.set_default(DEFAULT_TELEGRAM_BOT_KEY, new_default_bot)

            if new_default_bot:
                frappe.msgprint(
                    frappe._(f"Set {new_default_bot} as the default bot for notifications.")
                )

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

    def validate_api_token(self):
        if not self.is_new() and not self.has_value_changed("api_token"):
            return

        from telegram.ext import ExtBot
        try:
            bot = ExtBot(
                token=self.api_token
            )
            user = bot.get_me()
            if not user.is_bot:
                raise Exception(frappe._("TelegramUser is not a Bot"))
            self.username = "@" + user.username
        except BaseException as e:
            frappe.throw(msg=frappe._("Error with Bot Token: {0}").format(str(e)))
