# Copyright (c) 2021, Leam Technology Systems and Contributors
# See license.txt

import unittest
from re import template

import frappe
from frappe.exceptions import ValidationError
from frappe_telegram.client import send_message_from_template
from frappe_telegram.frappe_telegram.doctype.telegram_user.test_telegram_user import \
    TelegramUserFixtures
from frappe_telegram.utils.test_fixture import TestFixture


class TelegramMessageTemplateFixtures(TestFixture):

    def __init__(self):
        super().__init__()

        self.DEFAULT_DOCTYPE = "Telegram Message Template"
        self.dependent_fixtures = [
            TelegramUserFixtures
        ]

    def make_fixtures(self):

        fix_1 = frappe.get_doc(frappe._dict(
            doctype=self.DEFAULT_DOCTYPE,
            template_name="Test Template 1",
            default_template="This is a test template {{test}}"
        )).insert()
        self.add_document(fix_1)

        fix_2 = frappe.get_doc(frappe._dict(
            doctype=self.DEFAULT_DOCTYPE,
            template_name="Test Template 2",
            default_template="This is a test template {{test}}",
            template_translations=[
                frappe._dict(
                    language="ja",
                    template='This is the translation {{test}}'
                )
            ]
        )).insert()
        self.add_document(fix_2)


class TestTelegramMessageTemplate(unittest.TestCase):

    templates = TelegramMessageTemplateFixtures()

    def setUp(self) -> None:
        self.templates.setUp()

    def tearDown(self) -> None:
        self.templates.tearDown()

    def test_send_message_from_template(self):
        "Test the send_message_from_template client method"

        templates = self.templates.fixtures.get("Telegram Message Template")

        # Send a message with wrong template name
        with self.assertRaises(ValidationError):
            send_message_from_template("randomTemplateDNE")

        # Send a message with wrong template name + non existing lang
        with self.assertRaises(ValidationError):
            send_message_from_template("randomTemplateDNE", lang="randonlang")

        # TODO: How to set up a Telegram User?
        # TODO: How to send messages and confirm their output?

        # # Send a message with right name + non existing lang
        # with self.assertRaises(ValidationError):
        #     send_message_from_template(
        #         templates[1].name,
        #         {"test": "like this"},
        #         lang="randomlang"
        #     )

        # # Send a message with right name
        # send_message_from_template(
        #     templates[0].name,
        #     {"test": "like this"},
        #     telegram_user=self.templates.get_dependencies("Telegram User")[0].name
        # )

        # # Send a message with right name + existing lang
        # send_message_from_template(
        #     templates[1].name,
        #     {"test": "like this"},
        #     templates[1].template_translations[0].language,
        #     telegram_user=self.templates.get_dependencies("Telegram User")[0].name
        # )
