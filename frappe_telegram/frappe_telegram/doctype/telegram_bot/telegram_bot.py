# Copyright (c) 2021, Leam Technology Systems and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TelegramBot(Document):
    def autoname(self):
        self.name = self.title.replace(" ", "-")
