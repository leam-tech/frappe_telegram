# Copyright (c) 2021, Leam Technology Systems and Contributors
# See license.txt

import unittest

import frappe
from frappe_telegram.frappe_telegram.doctype.telegram_bot import DEFAULT_TELEGRAM_BOT_KEY
from frappe_testing.test_fixture import TestFixture


class TelegramBotFixtures(TestFixture):
    def __init__(self):
        super().__init__()
        self.DEFAULT_DOCTYPE = "Customer Document Type"

    def make_fixtures(self):

        # Some fixtures that have not been inserted

        fix1 = frappe.get_doc(frappe._dict(
            doctype="Telegram Bot",
            title="TestBotFix1",
            api_token="randonapitoken"
        ))
        self.add_document(fix1)

        fix2 = frappe.get_doc(frappe._dict(
            doctype="Telegram Bot",
            title="TestBotFix2",
            api_token="otherrandonapitoken"
        ))
        self.add_document(fix2)

        fix3 = frappe.get_doc(frappe._dict(
            doctype="Telegram Bot",
            title="TestBotFix3",
            api_token="anotherrandonapitoken"
        ))
        self.add_document(fix3)


class TestTelegramBot(unittest.TestCase):

    telegram_bots = TelegramBotFixtures()

    def setUp(self):
        self.telegram_bots.setUp()

    def tearDown(self):
        self.telegram_bots.tearDown()

    def test_auto_default_on_first_bot(self):
        """
        Test that if a new bot is created, it is marked as default if no other bot exists
        Also test that if that default is deleted, another one is marked default
        """

        existing_bots = frappe.get_all("Telegram Bot")
        self.assertEqual(len(existing_bots), 0)  # Test assumes there are no bots existing

        # Check the current default
        self.assertIsNone(frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY))

        # Load the unsaved fixtures
        fixture_bots = self.telegram_bots.fixtures.get("Telegram Bot")

        # Insert one
        bot1 = fixture_bots[0]
        bot1.insert()

        # Check if it has been made default
        self.assertEqual(frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY), bot1.title)

        # Insert another
        bot2 = fixture_bots[1]
        bot2.insert()

        # Check that the default is unchanged
        self.assertEqual(frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY), bot1.title)

        # Add and remove a bot
        bot3 = fixture_bots[2]
        bot3.insert()
        bot3.reload()
        bot3.delete()

        # Check that the default is unchanged
        self.assertEqual(frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY), bot1.title)

        # Remove the default
        bot1.reload()
        bot1.delete()

        # Check that the default is updated
        self.assertEqual(frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY), bot2.title)

        # Remove all bots
        bot2.reload()
        bot2.delete()

        # Check that default was set to none
        self.assertIsNone(frappe.db.get_default(DEFAULT_TELEGRAM_BOT_KEY))
