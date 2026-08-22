#!/usr/bin/env python3
"""
Unit tests for setup_git_hooks.py using Python standard library.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from setup_git_hooks import HOOKS_DIRNAME, PRE_PUSH_NAME, setup_git_hooks


class TestSetupGitHooks(unittest.TestCase):

    def test_setup_git_hooks_sets_hooks_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = Path(tmp_dir)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            hooks_dir = repo / HOOKS_DIRNAME
            hooks_dir.mkdir()
            hook = hooks_dir / PRE_PUSH_NAME
            hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

            success = setup_git_hooks(repo)
            self.assertTrue(success)

            result = subprocess.run(
                ["git", "-C", str(repo), "config", "--get", "core.hooksPath"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(result.stdout.strip(), HOOKS_DIRNAME)
            self.assertTrue(hook.stat().st_mode & 0o111)

    def test_setup_git_hooks_rejects_missing_hook(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = Path(tmp_dir)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            self.assertFalse(setup_git_hooks(repo))

    def test_setup_git_hooks_rejects_non_git_dir(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.assertFalse(setup_git_hooks(Path(tmp_dir)))


if __name__ == "__main__":
    unittest.main()
