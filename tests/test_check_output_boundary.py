#!/usr/bin/env python3
"""
Unit tests for check_output_boundary.py script.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from check_output_boundary import scan_file, scan_target


class TestCheckOutputBoundary(unittest.TestCase):

    def test_clean_manuscript(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Chapter 1: Introduction\n\nThis paper examines non-inclusive growth in the Philippines.\nWe address statistical artifact hypotheses.\n")
            temp_path = Path(f.name)

        try:
            violations = scan_file(temp_path)
            self.assertEqual(len(violations), 0)
        finally:
            temp_path.unlink()

    def test_forbidden_terms_detection(self):
        sample_content = """# Chapter 2
Line 2: This argument follows TDD methodology.
Line 3: In Red Phase, we list objections.
Line 4: 本文中にテストケースを含める。
Line 5: フェーズ1の検証結果を示す。
"""
        with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(sample_content)
            temp_path = Path(f.name)

        try:
            violations = scan_file(temp_path)
            self.assertEqual(len(violations), 4)
            detected_terms = [v[1].lower() for v in violations]
            self.assertIn("tdd", detected_terms)
            self.assertIn("red phase", detected_terms)
            self.assertIn("テストケース", detected_terms)
            self.assertIn("フェーズ1", detected_terms)
        finally:
            temp_path.unlink()

    def test_exclude_design_docs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            chapter_file = tmp_path / "chapter1.md"
            chapter_file.write_text("# Chapter 1\nClean text.\n", encoding="utf-8")

            design_file = tmp_path / "test-cases.md"
            design_file.write_text("# Test Cases\nTDD Red Phase internal doc.\n", encoding="utf-8")

            violations = scan_target(tmp_path)
            self.assertEqual(len(violations), 0)


if __name__ == '__main__':
    unittest.main()
