#!/usr/bin/env python3
"""Unit tests for check_terminology_consistency.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_terminology_consistency.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import check_terminology_consistency as ctc  # noqa: E402

GLOSSARY = """# 用語集

| 日本語 | English | 1行定義 |
| :--- | :--- | :--- |
| 認知スキャフォールディング | Cognitive Scaffolding | 足場 |
| 実行機能 | Executive Function (EF) | 前頭前野 |
| 主張の強度 | Modality | 断定度合い |

## A.3 コード表（パース対象外であること）

| コード | 意味 |
| :--- | :--- |
| **PROP-ADOPT** | AI 提案をそのまま採用 |
"""

CONFIG = """# 用語バリアント表
allowlist:
  - ScaffoldX

variants:
  - canonical: 主張の強度
    variants:
      - 主張トーン
    note: Modality gloss の統一
"""


class TestGlossaryParsing(unittest.TestCase):
    def test_pairs_extracted(self):
        terms, auto = ctc.parse_glossary_pairs(GLOSSARY)
        ja_en = {(t.ja, t.en) for t in terms}
        self.assertIn(("認知スキャフォールディング", "Cognitive Scaffolding"), ja_en)
        self.assertIn(("実行機能", "Executive Function"), ja_en)
        self.assertIn(("主張の強度", "Modality"), ja_en)

    def test_acronym_auto_allowlisted(self):
        _, auto = ctc.parse_glossary_pairs(GLOSSARY)
        self.assertIn("EF", auto)

    def test_code_table_not_parsed(self):
        terms, _ = ctc.parse_glossary_pairs(GLOSSARY)
        self.assertFalse(any("PROP" in t.en for t in terms))


class TestConfigLoading(unittest.TestCase):
    def test_load_subset_yaml(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "terminology-variants.yml"
            p.write_text(CONFIG, encoding="utf-8")
            cfg = ctc.load_config(p)
        self.assertIn("ScaffoldX", cfg.allowlist)
        self.assertEqual(len(cfg.variants), 1)
        canonical, variants, note = cfg.variants[0]
        self.assertEqual(canonical, "主張の強度")
        self.assertIn("主張トーン", variants)
        self.assertIn("Modality", note)

    def test_missing_config_is_empty(self):
        cfg = ctc.load_config(Path("/nonexistent/terminology-variants.yml"))
        self.assertEqual(cfg.variants, [])


class TestScanning(unittest.TestCase):
    def _scan(self, text: str):
        terms, auto = ctc.parse_glossary_pairs(GLOSSARY)
        cfg = ctc.Config(allowlist={"ScaffoldX"}, variants=[("主張の強度", ["主張トーン"], "")])
        allow = ctc.DEFAULT_ALLOWLIST | auto | cfg.allowlist
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "chapter.md"
            p.write_text(text, encoding="utf-8")
            return ctc.scan_file(p, terms, cfg, allow)

    def test_clean_glossed_prose_passes(self):
        findings = self._scan("本稿では主張の強度（Modality）を限定する。\n")
        self.assertEqual(findings, [])

    def test_bare_glossary_term_warns(self):
        findings = self._scan("ここで Modality 監査を行う。\n")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "WARN")
        self.assertEqual(findings[0].kind, "gloss")

    def test_bare_compound_term_detected(self):
        findings = self._scan("Modality監査という工程。\n")
        self.assertTrue(any(f.kind == "gloss" for f in findings))

    def test_definition_sentence_exempt(self):
        findings = self._scan("本節でいう **Modality** とは、主張の断定度合いを指す。\n")
        self.assertEqual(findings, [])

    def test_ja_earlier_on_line_is_glossed(self):
        findings = self._scan("主張の強度と範囲（Modality の限定）について述べる。\n")
        self.assertEqual(findings, [])

    def test_variant_is_fail(self):
        findings = self._scan("ゲートが主張トーンを較正した。\n")
        fails = [f for f in findings if f.severity == "FAIL"]
        self.assertEqual(len(fails), 1)
        self.assertEqual(fails[0].kind, "variant")

    def test_table_and_fence_exempt(self):
        text = (
            "| NC-05 | 主張トーンの較正 |\n"
            "\n"
            "```\n主張トーン\n```\n"
            "\n"
            "> 主張トーン\n"
        )
        self.assertEqual(self._scan(text), [])

    def test_ignore_marker_suppresses_line(self):
        text = "Modality 監査 <!-- terminology:ignore -->\n"
        self.assertEqual(self._scan(text), [])

    def test_allowlist_suppresses(self):
        text = "ScaffoldX を用いた。\n"
        self.assertEqual(self._scan(text), [])

    def test_generic_gloss_wrapper_exempt(self):
        text = "**適正オフローディング（Appropriate Cognitive Offloading）**の設計である。\n"
        self.assertEqual(self._scan(text), [])

    def test_reference_section_exempt(self):
        text = (
            "本文で Modality 監査と述べた。\n"
            "\n---\n\n## 参考文献\n\n"
            "- Den Houting, J. (2019). Neurodiversity: An insider's perspective.\n"
        )
        findings = self._scan(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].line, 1)


class TestCli(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True, text=True,
        )

    def test_fail_exit_code_on_variant(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "design/sot").mkdir(parents=True)
            (root / "design/sot/terminology-variants.yml").write_text(CONFIG, encoding="utf-8")
            (root / "literature").mkdir()
            (root / "literature/bilingual-glossary.md").write_text(GLOSSARY, encoding="utf-8")
            ch = root / "chapters"
            ch.mkdir()
            (ch / "c1.md").write_text("主張トーンを較正した。\n", encoding="utf-8")
            res = self._run(str(ch))
        self.assertEqual(res.returncode, 1)
        self.assertIn("FAILED", res.stderr)

    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "literature").mkdir()
            (root / "literature/bilingual-glossary.md").write_text(GLOSSARY, encoding="utf-8")
            ch = root / "chapters"
            ch.mkdir()
            (ch / "c1.md").write_text("主張の強度（Modality）を限定する。\n", encoding="utf-8")
            res = self._run(str(ch))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("PASSED", res.stdout)


if __name__ == "__main__":
    unittest.main()
