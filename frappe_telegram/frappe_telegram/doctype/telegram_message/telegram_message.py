# Copyright (c) 2021, Leam Technology Systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TelegramMessage(Document):
    def after_insert(self):
        self.update_last_message_on()

    def update_last_message_on(self):
        chat = frappe.get_doc("Telegram Chat", self.chat)
        chat.last_message_on = self.creation
        chat.last_message_content = self.content
        chat.save(ignore_permissions=True)
