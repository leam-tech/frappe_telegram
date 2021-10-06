# Copyright (c) 2021, Leam Technology Systems and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TelegramBot(Document):
    def autoname(self):
        self.name = self.title.replace(" ", "-")

    def validate(self):
        self.set_nginx_path()

    def set_nginx_path(self):
        if self.webhook_nginx_path:
            return

        if not self.webhook_url:
            return

        self.webhook_nginx_path = "/" + self.webhook_url.rstrip("/").split("/")[-1]
