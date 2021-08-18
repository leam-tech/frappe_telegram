import frappe
from frappe_telegram import Update, CallbackContext


def init_frappe(site: str):
    def _init(update: Update, context: CallbackContext):
        frappe.init(site=site)
        frappe.connect()

    return _init


def dispose_frappe(update: Update, context: CallbackContext):
    frappe.db.commit()
    frappe.destroy()