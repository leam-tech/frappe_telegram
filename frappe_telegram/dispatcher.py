import frappe
from telegram.ext import Dispatcher


"""
For each incoming Update, we will have frappe initialized.
The following Dispatcher Class overrides the default behavior

NOTE:
    Class attributes that starts with __ is Mangled
"""


class FrappeTelegramDispatcher(Dispatcher):

    # The Frappe Site
    site: str

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
            self.logger.debug('Processing Update: %s', update)
            self.process_update(update)
            self.update_queue.task_done()
            frappe.db.commit()
            frappe.destroy()

        self.running = False
        self.logger.debug('Dispatcher thread stopped')
