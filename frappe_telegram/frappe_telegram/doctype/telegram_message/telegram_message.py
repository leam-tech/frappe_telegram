# Copyright (c) 2021, Leam Technology Systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from telegram import Bot


class TelegramMessage(Document):
    def after_insert(self):
        self.update_last_message_on()

    def mark_as_password(self):
        self.db_set("content", "*" * len(self.content))
        if not getattr(frappe.flags, "in_telegram_update", None):
            return

        # Let's delete the message from the User's Chat
        chat = frappe.get_doc("Telegram Chat", self.chat)
        bot: Bot = chat.get_bot()
        try:
            bot.delete_message(chat_id=chat.chat_id, message_id=self.message_id)
        except Exception:
            pass

    def update_last_message_on(self):
        chat = frappe.get_doc("Telegram Chat", self.chat)
        chat.last_message_on = self.creation
        chat.last_message_content = self.content
        chat.save(ignore_permissions=True)
