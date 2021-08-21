import frappe
from telegram.ext import Dispatcher, ExtBot, Updater
from frappe_telegram.handlers.logging import log_outgoing_message


"""
For each incoming Update, we will have frappe initialized.
We will override Dispatcher and Bot instance
- Dispatcher is overridden for initializing frappe for each incoming Update
- Bot is overridden for loggign outgoing messages
NOTE:
    Class attributes that starts with __ is Mangled
"""


class FrappeTelegramExtBot(ExtBot):

    # The name of the active FrappeTelegramBot
    telegram_bot: str

    @classmethod
    def make(cls, telegram_bot: str, updater: Updater):
        bot = updater.bot
        new_bot = cls(
            bot.token,
            bot.base_url,
            request=updater._request,
            defaults=bot.defaults,
            arbitrary_callback_data=bot.arbitrary_callback_data,
        )
        new_bot.base_url = bot.base_url
        new_bot.base_file_url = bot.base_file_url
        new_bot.private_key = bot.private_key
        new_bot.telegram_bot = telegram_bot
        return new_bot

    def _message(self, *args, **kwargs):
        result = super()._message(*args, **kwargs)
        log_outgoing_message(self.telegram_bot, result)
        return result


class FrappeTelegramDispatcher(Dispatcher):

    # The Frappe Site
    site: str

    @classmethod
    def make(cls, site, updater):
        dispatcher = updater.dispatcher
        return cls(
            site,
            updater.bot,
            updater.update_queue,
            job_queue=updater.job_queue,
            workers=dispatcher.workers,
            # Class attributes that starts with __ is Mangled
            exception_event=updater._Updater__exception_event,
            persistence=dispatcher.persistence,
            use_context=dispatcher.use_context,
            context_types=dispatcher.context_types,
        )

    def __init__(self, site, *args, **kwargs):
        self.site = site
        print("Using Patched Frappe Telegram Dispatcher ✅")
        return super().__init__(*args, **kwargs)

    def process_update(self, update: object) -> None:
        try:
            frappe.init(site=self.site)
            frappe.connect()
            super().process_update(update=update)
        except BaseException:
            frappe.log_error(title="Telegram Process Update Error", message=frappe.get_traceback())
        finally:
            frappe.db.commit()
            frappe.destroy()
