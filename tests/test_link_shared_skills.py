#!/usr/bin/env python3
"""
Unit test for link_shared_skills.py script using Python standard library.
"""

import sys
import unittest
import tempfile
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from link_shared_skills import link_shared_skills


class TestLinkSharedSkills(unittest.TestCase):

    def test_link_shared_skills_execution(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_dir = Path(tmp_dir) / "target_repo"
            target_dir.mkdir()

            success = link_shared_skills(target_dir)
            self.assertTrue(success)

            # Check that symlinks exist
            self.assertTrue((target_dir / "skills").is_symlink())
            self.assertTrue((target_dir / "rules").is_symlink())
            self.assertTrue((target_dir / ".cursor" / "skills").is_symlink())
            self.assertTrue((target_dir / ".cursor" / "rules").is_symlink())
            self.assertTrue((target_dir / ".claude" / "skills").is_symlink())
            self.assertTrue((target_dir / ".agents" / "skills").is_symlink())
            self.assertTrue((target_dir / "AGENTS.md").is_symlink())
            self.assertTrue((target_dir / "CLAUDE.md").is_symlink())


if __name__ == "__main__":
    unittest.main()
