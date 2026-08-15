#!/usr/bin/env python3
"""
Unit test for setup_submodule.py script using Python standard library.
"""

import sys
import unittest
import tempfile
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from setup_submodule import setup_submodule_links


class TestSetupSubmodule(unittest.TestCase):

    def test_setup_submodule_execution(self):
        repo_root = Path(__file__).parent.parent

        with tempfile.TemporaryDirectory() as tmp_dir:
            parent_repo = Path(tmp_dir) / "parent_paper_repo"
            parent_repo.mkdir()
            submodule_dir = parent_repo / ".scholarly-agent-skills"

            # Create mock submodule directory structure
            submodule_dir.mkdir()
            (submodule_dir / "scripts").mkdir()
            (submodule_dir / "skills").mkdir()
            (submodule_dir / "rules").mkdir()
            (submodule_dir / "AGENTS.md").write_text("# AGENTS", encoding="utf-8")
            (submodule_dir / "CLAUDE.md").write_text("# CLAUDE", encoding="utf-8")

            # Copy setup_submodule.py to mock submodule scripts
            (submodule_dir / "scripts" / "setup_submodule.py").write_text(
                (repo_root / "scripts" / "setup_submodule.py").read_text(encoding="utf-8"),
                encoding="utf-8"
            )

            # Test setup_submodule_links function
            success = setup_submodule_links(parent_repo)
            self.assertTrue(success)

            # Verify relative symlinks in parent repo
            self.assertTrue((parent_repo / "skills").is_symlink())
            self.assertTrue((parent_repo / "rules").is_symlink())
            self.assertTrue((parent_repo / ".cursor" / "skills").is_symlink())
            self.assertTrue((parent_repo / ".cursor" / "rules").is_symlink())
            self.assertTrue((parent_repo / ".claude" / "skills").is_symlink())
            self.assertTrue((parent_repo / ".agents" / "skills").is_symlink())
            self.assertTrue((parent_repo / "AGENTS.md").is_symlink())
            self.assertTrue((parent_repo / "CLAUDE.md").is_symlink())


if __name__ == "__main__":
    unittest.main()
