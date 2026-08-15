#!/usr/bin/env python3
"""
Unit tests for check_skill_quality.py using Python standard library.
"""

import sys
import unittest
import tempfile
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from check_skill_quality import validate_skill_file, validate_skills_dir, validate_lang_parity


class TestCheckSkillQuality(unittest.TestCase):

    def test_valid_skill_file(self):
        content = """---
name: test-skill
version: 1.0.0
description: Use when testing a skill description
---

# Test Skill

## Purpose
Content goes here.

## Outputs
- `docs/output.md`
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "SKILL.md"
            tmp_path.write_text(content, encoding="utf-8")

            errors = validate_skill_file(tmp_path, expected_dir_name="test-skill")
            self.assertEqual(errors, [])

    def test_missing_frontmatter(self):
        content = """# Test Skill without frontmatter
Content goes here.
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "SKILL.md"
            tmp_path.write_text(content, encoding="utf-8")

            errors = validate_skill_file(tmp_path)
            self.assertTrue(any("frontmatter" in e for e in errors))

    def test_missing_name_or_description(self):
        content = """---
name: test-skill
version: 1.0.0
---
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "SKILL.md"
            tmp_path.write_text(content, encoding="utf-8")

            errors = validate_skill_file(tmp_path)
            self.assertTrue(any("description" in e for e in errors))

    def test_name_directory_mismatch(self):
        """Test that mismatched name: field and directory name is detected."""
        content = """---
name: wrong-name
version: 1.0.0
description: Use when testing a skill
---

# Test Skill

## Purpose
Content here.

## Outputs
- output
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "SKILL.md"
            tmp_path.write_text(content, encoding="utf-8")

            errors = validate_skill_file(tmp_path, expected_dir_name="correct-name")
            self.assertTrue(any("does not match" in e for e in errors))

    def test_name_directory_match(self):
        """Test that matching name: field and directory name passes."""
        content = """---
name: my-skill
version: 1.0.0
description: Use when testing a skill
---

# Test Skill

## Purpose
Content here.

## Outputs
- output
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "SKILL.md"
            tmp_path.write_text(content, encoding="utf-8")

            errors = validate_skill_file(tmp_path, expected_dir_name="my-skill")
            self.assertEqual(errors, [])

    def test_missing_purpose_section(self):
        """Test that missing Purpose/目的 section is detected."""
        content = """---
name: test-skill
version: 1.0.0
description: Use when testing a skill
---

# Test Skill

Some content without a purpose section.

## Outputs
- output
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "SKILL.md"
            tmp_path.write_text(content, encoding="utf-8")

            errors = validate_skill_file(tmp_path, expected_dir_name="test-skill")
            self.assertTrue(any("Purpose" in e or "目的" in e for e in errors))

    def test_japanese_purpose_section_accepted(self):
        """Test that Japanese '## 目的' section is accepted."""
        content = """---
name: test-skill
version: 1.0.0
description: テスト実行時に使用するスキル
---

# テストスキル

## 目的
内容がここにあります。

## 成果物
- `docs/output.md`
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "SKILL.md"
            tmp_path.write_text(content, encoding="utf-8")

            errors = validate_skill_file(tmp_path, expected_dir_name="test-skill")
            self.assertEqual(errors, [])

    def test_missing_outputs_section(self):
        """Test that missing Outputs/成果物 section generates a warning."""
        content = """---
name: test-skill
version: 1.0.0
description: Use when testing a skill
---

# Test Skill

## Purpose
Content here.
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "SKILL.md"
            tmp_path.write_text(content, encoding="utf-8")

            errors = validate_skill_file(tmp_path, expected_dir_name="test-skill")
            self.assertTrue(any("Outputs" in e or "成果物" in e for e in errors))

    def test_validate_skills_dir(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            skill_folder = Path(tmp_dir) / "sample-skill"
            skill_folder.mkdir()
            (skill_folder / "SKILL.md").write_text(
                "---\nname: sample-skill\nversion: 1.0.0\ndescription: Use when testing sample\n---\n\n## Purpose\nTest.\n\n## Outputs\n- out\n",
                encoding="utf-8"
            )

            count, errors, names = validate_skills_dir(Path(tmp_dir))
            self.assertEqual(count, 1)
            self.assertEqual(errors, 0)
            self.assertEqual(names, ["sample-skill"])

    def test_lang_parity_matching(self):
        """Test that identical ja/en directories pass parity check."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            for lang in ["ja", "en"]:
                for skill in ["skill-a", "skill-b"]:
                    (root / lang / skill).mkdir(parents=True)

            parity_errors = validate_lang_parity(root)
            self.assertEqual(parity_errors, 0)

    def test_lang_parity_mismatch(self):
        """Test that differing ja/en directories are detected."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "ja" / "skill-a").mkdir(parents=True)
            (root / "ja" / "skill-b").mkdir(parents=True)
            (root / "en" / "skill-a").mkdir(parents=True)
            # skill-b missing in en/

            parity_errors = validate_lang_parity(root)
            self.assertEqual(parity_errors, 1)


if __name__ == "__main__":
    unittest.main()
