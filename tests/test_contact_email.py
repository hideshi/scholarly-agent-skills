#!/usr/bin/env python3
"""
Unit tests for contact_email.py outbound User-Agent policy.
Uses ONLY Python standard library.
"""

import sys
import os
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from contact_email import (
    ContactEmailError,
    CONTACT_EMAIL_SETUP_MESSAGE,
    is_usable_contact_email,
    require_contact_email,
    resolve_contact_email,
)


class TestContactEmail(unittest.TestCase):

    def test_rejects_empty_and_placeholders(self):
        for value in (
            "",
            "   ",
            "not-an-email",
            "you@example.com",
            "user@example.org",
            "name@example.net",
            "dev@localhost",
        ):
            self.assertFalse(is_usable_contact_email(value), msg=value)

    def test_accepts_institutional_address(self):
        self.assertTrue(is_usable_contact_email("firstname.lastname@university.ac.jp"))

    def test_require_contact_email_raises_actionable_error(self):
        env_without_contact = {
            key: value for key, value in os.environ.items() if key != "SCHOLARLY_CONTACT_EMAIL"
        }
        with patch.dict(os.environ, env_without_contact, clear=True):
            with self.assertRaises(ContactEmailError) as ctx:
                require_contact_email({})
            message = str(ctx.exception)
            self.assertIn("export SCHOLARLY_CONTACT_EMAIL=", message)
            self.assertIn("Ask the user", message)
            self.assertIn("ユーザーに実メールを確認", message)
            self.assertEqual(message, CONTACT_EMAIL_SETUP_MESSAGE)

    def test_require_contact_email_rejects_dummy_env(self):
        with patch.dict(os.environ, {"SCHOLARLY_CONTACT_EMAIL": "you@example.com"}):
            with self.assertRaises(ContactEmailError):
                require_contact_email()

    def test_require_contact_email_accepts_real_env(self):
        with patch.dict(os.environ, {"SCHOLARLY_CONTACT_EMAIL": "firstname.lastname@university.ac.jp"}):
            self.assertEqual(
                require_contact_email(),
                "firstname.lastname@university.ac.jp",
            )

    def test_resolve_contact_email_prefers_env(self):
        with patch.dict(os.environ, {"SCHOLARLY_CONTACT_EMAIL": "env@university.ac.jp"}):
            self.assertEqual(
                resolve_contact_email({"contact_email": "config@university.ac.jp"}),
                "env@university.ac.jp",
            )

    def test_resolve_contact_email_uses_config_when_env_absent(self):
        env_without_contact = {
            key: value for key, value in os.environ.items() if key != "SCHOLARLY_CONTACT_EMAIL"
        }
        with patch.dict(os.environ, env_without_contact, clear=True):
            self.assertEqual(
                resolve_contact_email({"contact_email": "config@university.ac.jp"}),
                "config@university.ac.jp",
            )
            self.assertEqual(resolve_contact_email({}), "")


if __name__ == "__main__":
    unittest.main()
