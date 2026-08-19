#!/usr/bin/env python3
"""Unit tests for check_reviewer_readability.py (stdlib only)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from check_reviewer_readability import main, scan_file, scan_target  # noqa: E402


def write_temp(content: str) -> Path:
    f = tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return Path(f.name)


class TestProseScanning(unittest.TestCase):
    def tearDown(self):
        if getattr(self, "tmp", None):
            self.tmp.unlink(missing_ok=True)

    def scan(self, content: str):
        self.tmp = write_temp(content)
        return scan_file(self.tmp)

    def test_clean_prose_passes(self):
        findings = self.scan("# 序論\n\n本研究は設計命題の存在例を示す。\n")
        self.assertEqual(findings, [])

    def test_bare_code_in_prose_is_fail(self):
        findings = self.scan("著者は PROP-ADOPT を記録した。\n")
        self.assertTrue(any(f.severity == "FAIL" and f.kind == "code" for f in findings))

    def test_parenthesized_code_gloss_passes(self):
        findings = self.scan("用語確認の質問（`RQ-TERM`）が観察された。\n")
        self.assertEqual(findings, [])

    def test_nc_as_subject_is_fail(self):
        findings = self.scan("NC-09 は二読しうる。\n")
        self.assertTrue(any(f.severity == "FAIL" and f.kind == "nc" for f in findings))

    def test_nc_parenthesized_passes(self):
        findings = self.scan("この依存申告（NC-09）は二読しうる。\n")
        self.assertEqual(findings, [])

    def test_nc_followed_by_gloss_passes(self):
        findings = self.scan("同日中に NC-01（図表の却下）が記録された。\n")
        self.assertEqual(findings, [])

    def test_jst_in_prose_is_warn(self):
        findings = self.scan("15:32 JST に固定された。\n")
        self.assertTrue(any(f.severity == "WARN" and f.kind == "jst" for f in findings))
        self.assertFalse(any(f.severity == "FAIL" for f in findings))

    def test_version_in_prose_is_warn(self):
        findings = self.scan("v2.4.0 以降、プロトコルが変更された。\n")
        self.assertTrue(any(f.severity == "WARN" and f.kind == "version" for f in findings))

    def test_jargon_bare_is_warn_but_gloss_exempt(self):
        bare = self.scan("引用の grounding を検査する。\n")
        self.assertTrue(any(f.kind == "jargon" for f in bare))
        glossed = self.scan("文献実体化（grounding）を検査する。\n")
        self.assertFalse(any(f.kind == "jargon" for f in glossed))

    def test_density_warn(self):
        findings = self.scan("主語として PROP-ADOPT PROP-REJECT PROP-INIT を並べる。\n")
        self.assertTrue(any(f.kind == "density" for f in findings))

    def test_table_blockquote_fence_exempt(self):
        content = (
            "| `PROP-ADOPT` | 提案採択 |\n"
            "\n"
            "> **表注**: `SCAF-FAIL`＝非機能。\n"
            "\n"
            "```\n"
            "NC-01 はコードブロック内。\n"
            "```\n"
        )
        findings = self.scan(content)
        self.assertEqual(findings, [])

    def test_ignore_marker_skips_line(self):
        findings = self.scan("15:32 JST に固定された。 <!-- readability:ignore -->\n")
        self.assertEqual(findings, [])


class TestSectionNumbering(unittest.TestCase):
    def tearDown(self):
        if getattr(self, "tmp", None):
            self.tmp.unlink(missing_ok=True)

    def scan(self, content: str):
        self.tmp = write_temp(content)
        return scan_file(self.tmp)

    def test_branch_heading_is_fail(self):
        findings = self.scan("## 3.2 制度文の断面\n\n## 3.2b 追加の断面\n")
        self.assertTrue(any(f.severity == "FAIL" and f.kind == "secnum-branch" for f in findings))

    def test_branch_reference_in_prose_is_fail(self):
        findings = self.scan("## 3.2b 追加\n\n詳細は §3.2b を参照。\n")
        fails = [f for f in findings if f.kind == "secnum-branch"]
        self.assertTrue(any(f.match == "3.2b" for f in fails))

    def test_clean_sequence_passes(self):
        findings = self.scan("## 3.1 導入\n\n## 3.2 展開\n\n## 3.3 まとめ\n\n§3.1 で述べた。\n")
        self.assertFalse(any(f.kind.startswith("secnum") for f in findings))

    def test_gap_is_warn(self):
        findings = self.scan("## 3.1 導入\n\n## 3.3 まとめ\n")
        gaps = [f for f in findings if f.kind == "secnum-gap"]
        self.assertTrue(gaps and gaps[0].severity == "WARN" and "3.2" in gaps[0].match)

    def test_duplicate_heading_is_fail(self):
        findings = self.scan("## 4.1 前提\n\n## 4.1 重複した見出し\n")
        self.assertTrue(any(f.severity == "FAIL" and f.kind == "secnum-dup" for f in findings))

    def test_dangling_reference_is_warn(self):
        findings = self.scan("## 5.1 前提\n\n§5.2 で検討する。\n")
        self.assertTrue(any(f.kind == "secnum-dangling" and f.match == "§5.2" for f in findings))

    def test_three_level_external_ref_passes(self):
        findings = self.scan("## 4.1 前提\n\n先行研究（小越 2026, §2.1.1）を参照。\n")
        self.assertFalse(any(f.kind == "secnum-dangling" for f in findings))

    def test_branch_insertion_pattern_no_gap_no_dup(self):
        content = "## 3.1 導入\n\n## 3.2 制度文\n\n## 3.2b 追加\n\n## 3.3 まとめ\n"
        findings = self.scan(content)
        self.assertFalse(any(f.kind in ("secnum-gap", "secnum-dup") for f in findings))
        self.assertTrue(any(f.kind == "secnum-branch" for f in findings))

    def test_cross_file_reference_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "chapter3.md").write_text("## 3.1 導入\n", encoding="utf-8")
            (d / "chapter4.md").write_text("## 4.1 前提\n\n§3.1 を踏まえる。\n", encoding="utf-8")
            findings = scan_target(d)
            self.assertFalse(any(f.kind == "secnum-dangling" for f in findings))


class TestMainAndTarget(unittest.TestCase):
    def test_main_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "chapter.md"
            target.write_text("NC-09 が主語の文。\n", encoding="utf-8")
            self.assertEqual(main([str(target)]), 1)
            target.write_text("負例（NC-09）を参照。\n", encoding="utf-8")
            self.assertEqual(main([str(target)]), 0)

    def test_scan_target_excludes_design_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "chapter1.md").write_text("# 序論\n\n本文。\n", encoding="utf-8")
            (d / "test-cases.md").write_text("NC-01 は正本。PROP-ADOPT。\n", encoding="utf-8")
            findings = scan_target(d)
            self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
