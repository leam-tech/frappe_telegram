from .notification import add_telegram_notification_channel


def after_install():
    add_telegram_notification_channel()


def after_migrate():
    add_telegram_notification_channel()
