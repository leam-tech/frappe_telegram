# Copyright (c) 2021, Leam Technology Systems and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TelegramChat(Document):
    def validate(self):
        pass

    def get_bot(self):
        if not len(self.bots):
            return None

        from frappe_telegram.client import get_bot
        return get_bot(self.bots[0].telegram_bot)
