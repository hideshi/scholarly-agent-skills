#!/usr/bin/env python3
"""
Unit tests for check_citation_format.py using ONLY Python standard library.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to sys.path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "scripts"))

from check_citation_format import (
    check_citations_in_file,
    extract_citations_from_text,
    generate_references_markdown,
    parse_literature_matrix,
)


class TestCheckCitationFormat(unittest.TestCase):

    def test_extract_citations_institutional_authors(self):
        """Test that institutional acronyms (PSA, ADB) and multi-word names (World Bank) are extracted."""
        text = (
            "The per capita GRDP in NCR was 2.3x higher than national average (PSA, 2024).\n"
            "Growth elasticity was low (World Bank, 2026; Son, 2010).\n"
            "4Ps coverage is east asia largest (DSWD, 2024; ADB, 2023).\n"
        )
        citations = extract_citations_from_text(text)
        authors = [c[0] for c in citations]
        years = [c[1] for c in citations]

        self.assertIn("PSA", authors)
        self.assertIn("World Bank", authors)
        self.assertIn("Son", authors)
        self.assertIn("DSWD", authors)
        self.assertIn("ADB", authors)
        self.assertIn("2024", years)
        self.assertIn("2026", years)

    def test_parse_literature_matrix_and_generate_references(self):
        """Test parsing literature-matrix.md and auto-generating references.md with AUTO-GENERATED header."""
        matrix_sample = (
            "# Literature Matrix\n\n"
            "| DOI / Link | 文献名 / タイトル | 著者 (Authors) | 出版年 | 分析手法 | 主要発見 | 対象分類 | 信頼度評価 |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| [10.1596/41857](https://doi.org/10.1596/41857) | 4Ps Policy Note | World Bank | 2024 | Panel | Positive 4Ps impact | 4Ps | ★★★★★ |\n"
            "| [10.62986/dp2024](https://doi.org/10.62986/dp2024) | GRDP Accounts | PSA | 2024 | Survey | Spatial disparities | GRDP | ★★★★★ |\n"
        )

        with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(matrix_sample)
            f_path = Path(f.name)

        try:
            entries = parse_literature_matrix(f_path)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0]["author"], "World Bank")
            self.assertEqual(entries[1]["author"], "PSA")

            ref_markdown = generate_references_markdown(entries)
            self.assertIn("<!-- AUTO-GENERATED from docs/literature/literature-matrix.md. Do not edit manually. -->", ref_markdown)
            self.assertIn("- **PSA** (2024). *GRDP Accounts*", ref_markdown)
            self.assertIn("- **World Bank** (2024). *4Ps Policy Note*", ref_markdown)
        finally:
            f_path.unlink()


if __name__ == "__main__":
    unittest.main()
