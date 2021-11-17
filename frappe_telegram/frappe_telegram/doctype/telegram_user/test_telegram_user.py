# Copyright (c) 2021, Leam Technology Systems and Contributors
# See license.txt

import frappe
import unittest

from frappe_telegram.utils.test_fixture import TestFixture


class TelegramUserFixtures(TestFixture):

    def __init__(self):
        super().__init__()
        self.DEFAULT_DOCTYPE = "Telegram User"

    def make_fixtures(self):

        # TODO: How to make telegram user for testing? Mock values won't work

        # fix_1 = frappe.get_doc(
        #     doctype="Telegram User",
        #     telegram_user_id="10101010101010",
        #     telegram_username="@testfixfullname",
        #     full_name="test_fix_fullname"
        # ).insert(ignore_permissions=True)
        # frappe.db.commit()
        # self.add_document(fix_1)

        pass


class TestTelegramUser(unittest.TestCase):
    pass
