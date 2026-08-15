#!/usr/bin/env python3
"""
Unit tests for manage_user_config.py using ONLY Python standard library.
"""

import sys
import unittest
import tempfile
import json
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from manage_user_config import load_user_preferences, save_user_preferences


class TestManageUserConfig(unittest.TestCase):

    def test_load_default_fallback(self):
        prefs = load_user_preferences(Path("/nonexistent/path/prefs.json"))
        self.assertEqual(prefs["native_language"], "Japanese")
        self.assertEqual(prefs["language_code"], "ja")

    def test_save_and_load_custom_preferences(self):
        custom_data = {
            "native_language": "German",
            "language_code": "de",
            "translation_style": "academic_formal",
            "preserve_original_terms": True
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "test_prefs.json"
            success = save_user_preferences(custom_data, tmp_path)
            self.assertTrue(success)

            loaded = load_user_preferences(tmp_path)
            self.assertEqual(loaded["native_language"], "German")
            self.assertEqual(loaded["language_code"], "de")


if __name__ == "__main__":
    unittest.main()
