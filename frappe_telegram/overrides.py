import frappe
from telegram import TelegramError
from telegram.ext import Dispatcher, DispatcherHandlerStop, ExtBot, Updater
from telegram.utils.helpers import DEFAULT_FALSE
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
        return super().__init__(*args, **kwargs)

    def start(self, ready=None) -> None:
        """Thread target of thread 'dispatcher'.
        Runs in background and processes the update queue.
        Args:
            ready (:obj:`threading.Event`, optional): If specified, the event will be set once the
                dispatcher is ready.
        """
        from telegram import TelegramError
        from queue import Empty
        from uuid import uuid4

        print("Using Patched Frappe Telegram Dispatcher ✅")

        if self.running:
            self.logger.warning('already running')
            if ready is not None:
                ready.set()
            return

        if self._Dispatcher__exception_event.is_set():
            msg = 'reusing dispatcher after exception event is forbidden'
            self.logger.error(msg)
            raise TelegramError(msg)

        self._init_async_threads(str(uuid4()), self.workers)
        self.running = True
        self.logger.debug('Dispatcher started')

        if ready is not None:
            ready.set()

        while True:
            try:
                # Pop update from update queue.
                update = self.update_queue.get(True, 1)
            except Empty:
                if self._Dispatcher__stop_event.is_set():
                    self.logger.debug('orderly stopping')
                    break
                if self._Dispatcher__exception_event.is_set():
                    self.logger.critical('stopping due to exception in another thread')
                    break
                continue

            frappe.init(site=self.site)
            frappe.connect()
            context = self.context_types.context.from_update(update, self)
            context.refresh_data()

            try:
                self.logger.debug('Processing Update: %s', update)
                for cmd in frappe.get_hooks("telegram_pre_process_update"):
                    frappe.get_attr(cmd)(update, context)

                self.process_update(update, context)

                for cmd in frappe.get_hooks("telegram_post_process_update"):
                    frappe.get_attr(cmd)(update, context)
            except DispatcherHandlerStop:
                self.logger.debug('Stopping further handlers due to DispatcherHandlerStop')

            self.update_queue.task_done()
            frappe.db.commit()
            frappe.destroy()

        self.running = False
        self.logger.debug('Dispatcher thread stopped')

    def process_update(self, update: object, context) -> None:
        """Processes a single update and updates the persistence.

        Note:
            If the update is handled by least one synchronously running handlers (i.e.
            ``run_async=False``), :meth:`update_persistence` is called *once* after all handlers
            synchronous handlers are done. Each asynchronously running handler will trigger
            :meth:`update_persistence` on its own.

        Args:
            update (:class:`telegram.Update` | :obj:`object` | \
                :class:`telegram.error.TelegramError`):
                The update to process.

        """
        # An error happened while polling
        if isinstance(update, TelegramError):
            try:
                self.dispatch_error(None, update)
            except Exception:
                self.logger.exception('An uncaught error was raised while handling the error.')
            return

        # context = None
        handled = False
        sync_modes = []

        for group in self.groups:
            try:
                for handler in self.handlers[group]:
                    check = handler.check_update(update)
                    if check is not None and check is not False:
                        if not context and self.use_context:
                            context = self.context_types.context.from_update(update, self)
                            context.refresh_data()
                        handled = True
                        sync_modes.append(handler.run_async)
                        handler.handle_update(update, self, check, context)
                        break

            # Stop processing with any other handler.
            except DispatcherHandlerStop:
                self.logger.debug('Stopping further handlers due to DispatcherHandlerStop')
                self.update_persistence(update=update)
                break

            # Dispatch any error.
            except Exception as exc:
                try:
                    self.dispatch_error(update, exc)
                except DispatcherHandlerStop:
                    self.logger.debug('Error handler stopped further handlers')
                    break
                # Errors should not stop the thread.
                except Exception:
                    self.logger.exception('An uncaught error was raised while handling the error.')

        # Update persistence, if handled
        handled_only_async = all(sync_modes)
        if handled:
            # Respect default settings
            if all(mode is DEFAULT_FALSE for mode in sync_modes) and self.bot.defaults:
                handled_only_async = self.bot.defaults.run_async
            # If update was only handled by async handlers, we don't need to update here
            if not handled_only_async:
                self.update_persistence(update=update)
