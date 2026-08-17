#!/usr/bin/env python3
"""Unit tests for check_sensitive_expression.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_sensitive_expression.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import check_sensitive_expression as cse  # noqa: E402

CONFIG = """# センシティブ表現ルール
absolute_terms:
  - 無限に

banned_terms:
  - 無尽蔵

abstract_flagged:
  - 神経多様性

allowlist:
  - 障害|二項対立（
  - Task Initiation Deficit
"""

OUTLINE = """# 構成

## 1. アブストラクト（構想案 / Abstract）

本研究は認知傾向を認知スタイルのスペクトラムとして扱う。

---

## 2. RQ
"""


def prose_lines(text: str):
    return list(cse.iter_prose_blocks(text))


class TestConfigParsing(unittest.TestCase):
    def _write(self, tmp: Path, text: str) -> Path:
        p = tmp / "sensitive-expressions.yml"
        p.write_text(text, encoding="utf-8")
        return p

    def test_sections_loaded(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            cfg = cse.load_config(self._write(Path(d), CONFIG))
        self.assertIn("無限に", cfg.absolute)
        self.assertIn("無尽蔵", cfg.banned)
        self.assertIn("神経多様性", cfg.abstract_flagged)
        self.assertIn(("障害", "二項対立（"), cfg.allowlist)
        self.assertIn(("Task Initiation Deficit", None), cfg.allowlist)

    def test_missing_config(self):
        cfg = cse.load_config(None)
        self.assertEqual(cfg.banned, [])


class TestLineRules(unittest.TestCase):
    def setUp(self):
        self.cfg = cse.Config()

    def kinds(self, findings):
        return {f.kind for f in findings}

    def test_absolute_term_warns(self):
        f, _, _ = cse.scan_lines("t.md", prose_lines("この枠組みは常に有効である。"), self.cfg)
        self.assertIn("absolute", self.kinds(f))

    def test_quantifier_without_citation_warns(self):
        f, _, _ = cse.scan_lines("t.md", prose_lines("多くの実務家が直面する。"), self.cfg)
        self.assertIn("quantifier", self.kinds(f))

    def test_quantifier_with_citation_exempt(self):
        f, _, _ = cse.scan_lines("t.md", prose_lines("多くの実務家が直面する（Sato, 2020）。"), self.cfg)
        self.assertNotIn("quantifier", self.kinds(f))

    def test_modality_flagged(self):
        f, _, _ = cse.scan_lines("t.md", prose_lines("本研究は機構を解明する。"), self.cfg)
        self.assertIn("modality", self.kinds(f))

    def test_modality_future_work_exempt(self):
        f, _, _ = cse.scan_lines("t.md", prose_lines("機構の解明は将来の課題とする。"), self.cfg)
        self.assertNotIn("modality", self.kinds(f))

    def test_deficit_term_warns(self):
        f, _, _ = cse.scan_lines("t.md", prose_lines("それを障害から強みへ転換する。"), self.cfg)
        self.assertIn("deficit", self.kinds(f))

    def test_banned_term_fails(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.yml"
            p.write_text("banned_terms:\n  - 無尽蔵\n", encoding="utf-8")
            cfg = cse.load_config(p)
        f, _, _ = cse.scan_lines("t.md", prose_lines("アイデアが無尽蔵に湧く。"), cfg)
        banned = [x for x in f if x.kind == "banned"]
        self.assertEqual(len(banned), 1)
        self.assertEqual(banned[0].severity, "FAIL")

    def test_allowlist_context_suppresses(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.yml"
            p.write_text("allowlist:\n  - 障害|二項対立（\n", encoding="utf-8")
            cfg = cse.load_config(p)
        meta = "二項対立（障害/健常）を批判する。"
        other = "それは障害として扱われる。"
        f_meta, _, _ = cse.scan_lines("t.md", prose_lines(meta), cfg)
        f_other, _, _ = cse.scan_lines("t.md", prose_lines(other), cfg)
        self.assertNotIn("deficit", self.kinds(f_meta))
        self.assertIn("deficit", self.kinds(f_other))

    def test_table_and_fence_exempt(self):
        text = "| 障害 | 用語 |\n| --- | --- |\n| 障害 | x |\n\n```\n無尽蔵\n```\n"
        f, _, _ = cse.scan_lines("t.md", prose_lines(text), self.cfg)
        self.assertEqual(f, [])


class TestCooccurrence(unittest.TestCase):
    def setUp(self):
        self.cfg = cse.Config()

    def test_misidentification_coupling_warns(self):
        text = "著者自身は ADHD の特性を持つ。\n"
        f, saw_med, _ = cse.scan_lines("t.md", prose_lines(text), self.cfg)
        self.assertIn("misidentify", {x.kind for x in f})
        self.assertTrue(saw_med)

    def test_disclaimer_in_paragraph_exempts(self):
        text = "著者自身の経験を扱うが、診断の有無を問わず ADHD の文脈に限定しない。\n"
        f, _, saw_disc = cse.scan_lines("t.md", prose_lines(text), self.cfg)
        self.assertNotIn("misidentify", {x.kind for x in f})
        self.assertTrue(saw_disc)

    def test_separate_paragraphs_still_couple_risk_free(self):
        text = "著者自身の経験を述べる。\n\nADHD の文献をレビューする（Sato, 2020）。\n"
        f, _, _ = cse.scan_lines("t.md", prose_lines(text), self.cfg)
        self.assertNotIn("misidentify", {x.kind for x in f})


class TestAbstractScope(unittest.TestCase):
    def test_abstract_flagged_only_in_abstract(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            outline = Path(d) / "paper-outline.md"
            outline.write_text(OUTLINE, encoding="utf-8")
            lines = cse.extract_abstract_lines(outline)
        self.assertTrue(lines)
        cfg = cse.Config()
        f_abs, _, _ = cse.scan_lines("abstract", lines, cfg, scope="abstract")
        f_body, _, _ = cse.scan_lines("t.md", lines, cfg, scope="body")
        self.assertIn("abstract", {x.kind for x in f_abs})
        self.assertNotIn("abstract", {x.kind for x in f_body})


class TestCli(unittest.TestCase):
    def test_cli_exit_codes(self):
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            chapters = root / "chapters"
            chapters.mkdir()
            (chapters / "chapter1.md").write_text("本研究は機構を解明する。\n", encoding="utf-8")
            warn_run = subprocess.run(
                [sys.executable, str(SCRIPT), str(chapters), "--outline", "/nonexistent"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(warn_run.returncode, 0)
            self.assertIn("WARN", warn_run.stdout)

            (chapters / "chapter1.md").write_text(
                "banned_terms check\n", encoding="utf-8"
            )
            cfg = root / "design" / "sot"
            cfg.mkdir(parents=True)
            (cfg / "sensitive-expressions.yml").write_text(
                "banned_terms:\n  - banned_terms\n", encoding="utf-8"
            )
            fail_run = subprocess.run(
                [sys.executable, str(SCRIPT), str(chapters), "--outline", "/nonexistent"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(fail_run.returncode, 1)


if __name__ == "__main__":
    unittest.main()
