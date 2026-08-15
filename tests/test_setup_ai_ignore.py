#!/usr/bin/env python3
"""
Unit tests for setup_ai_ignore.py using ONLY Python standard library.
"""

import sys
import unittest
import tempfile
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from setup_ai_ignore import setup_ai_ignore


class TestSetupAiIgnore(unittest.TestCase):

    def test_setup_ai_ignore_creation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir)
            success = setup_ai_ignore(target_path)
            self.assertTrue(success)

            for filename in [".cursorignore", ".claudeignore", ".agentsignore", ".ignore"]:
                ignore_file = target_path / filename
                self.assertTrue(ignore_file.exists())
                content = ignore_file.read_text(encoding="utf-8")
                self.assertIn("raw_data/", content)
                self.assertIn("private_data/", content)


if __name__ == "__main__":
    unittest.main()
