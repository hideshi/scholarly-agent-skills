#!/usr/bin/env python3
"""
Unit tests for check_fact_grounding.py using ONLY Python standard library.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to sys.path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "scripts"))

from check_fact_grounding import find_ungrounded_claims


class TestCheckFactGrounding(unittest.TestCase):

    def test_year_and_section_exclusion(self):
        """Test that years (1945年, 2024) and section numbers (## 2.1.2) are excluded from false positive detection."""
        sample_text = (
            "# 1. Introduction\n\n"
            "## 2.1.2 Historical Context\n\n"
            "In 1945, the treaty was signed in Manila. In the 20th century, economic growth fluctuated.\n"
        )
        with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(sample_text)
            f_path = Path(f.name)

        try:
            violations = find_ungrounded_claims(f_path, repo_root)
            self.assertEqual(len(violations), 0)
        finally:
            f_path.unlink()

    def test_code_fence_exclusion(self):
        """Test that numbers inside markdown code blocks are ignored."""
        sample_text = (
            "# Code Example\n\n"
            "```bash\n"
            "python3 fetch_data.py --growth 7.5% --limit 10\n"
            "```\n"
        )
        with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(sample_text)
            f_path = Path(f.name)

        try:
            violations = find_ungrounded_claims(f_path, repo_root)
            self.assertEqual(len(violations), 0)
        finally:
            f_path.unlink()

    def test_harvard_citation_grounding(self):
        """Test that Harvard citations (Author, YYYY) and Japanese citations （PSA, 2024） are recognized as evidence."""
        sample_text = (
            "# Section 3\n\n"
            "The per capita GRDP in NCR was 2.3x higher than national average (PSA, 2024).\n\n"
            "また、ジニ係数は8ポイント低下した（World Bank, 2023）。\n"
        )
        with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(sample_text)
            f_path = Path(f.name)

        try:
            violations = find_ungrounded_claims(f_path, repo_root)
            self.assertEqual(len(violations), 0)
        finally:
            f_path.unlink()

    def test_quantitative_candidate_detection(self):
        """Test that ungrounded candidates like 2.3倍, 8ポイント低下, 15% without citations are detected."""
        sample_text = (
            "# Section 2\n\n"
            "This paragraph claims the NCR per capita GRDP reached 2.3倍 without any citation.\n\n"
            "Another statement says inequality dropped by 8ポイント without proof.\n"
        )
        with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(sample_text)
            f_path = Path(f.name)

        try:
            violations = find_ungrounded_claims(f_path, repo_root)
            self.assertEqual(len(violations), 2)
        finally:
            f_path.unlink()


if __name__ == "__main__":
    unittest.main()
