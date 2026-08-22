#!/usr/bin/env python3
"""Unit tests for assemble_manuscript.py (stdlib only)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from assemble_manuscript import (  # noqa: E402
    extract_biblio_lines,
    extract_titles,
    title_to_filename,
)


class TestAssembleManuscriptNaming(unittest.TestCase):
    def test_title_to_filename_uses_full_japanese_title(self):
        title = (
            "AIによる認知スキャフォールディングとアイデア発散傾向の構造化："
            "IT実務家における論文執筆の民主化と認知拡張メカニズム"
        )
        self.assertEqual(title_to_filename(title), f"{title}.md")

    def test_title_to_filename_sanitizes_halfwidth_path_chars(self):
        self.assertEqual(
            title_to_filename('A:B/C\\D*E?F"G<H>I|J'),
            "A：B／C＼D＊E？F＂G＜H＞I｜J.md",
        )

    def test_extract_titles_keeps_full_for_filename(self):
        outline = (
            "**論文仮題（和文）**: 主題：副題です\n"
            "**論文仮題（英文）**: Main: Subtitle\n"
        )
        ja_short, ja_full, en = extract_titles(outline)
        self.assertEqual(ja_short, "主題")
        self.assertEqual(ja_full, "主題：副題です")
        self.assertEqual(en, "Main: Subtitle")
        self.assertEqual(title_to_filename(ja_full), "主題：副題です.md")

    def test_extract_biblio_lines_optional(self):
        self.assertEqual(extract_biblio_lines("**論文仮題（和文）**: 題\n"), [])
        outline = (
            "**著者**: 小越 秀\n"
            "**所属**: なし（独立研究者）\n"
            "**日付**: 2026-08-22\n"
            "**ライセンス**: CC BY 4.0\n"
            "**バージョン**: v1.0.0\n"
            "**DOI**: 10.5281/zenodo.22054034\n"
        )
        self.assertEqual(
            extract_biblio_lines(outline),
            [
                "- **著者**: 小越 秀",
                "- **所属**: なし（独立研究者）",
                "- **日付**: 2026-08-22",
                "- **ライセンス**: CC BY 4.0",
                "- **バージョン**: v1.0.0",
                "- **DOI**: 10.5281/zenodo.22054034",
            ],
        )

    def test_default_output_path_is_not_paper_id(self):
        """Regression: deliverable must not be {paper-id}-draft.md."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paper = root / "docs" / "cognitive-scaffolding"
            (paper / "design" / "sot").mkdir(parents=True)
            (paper / "chapters").mkdir(parents=True)
            (paper / "manuscript").mkdir(parents=True)

            (paper / "design" / "sot" / "paper-outline.md").write_text(
                "**論文仮題（和文）**: 正式タイトル例：副題\n"
                "**論文仮題（英文）**: Official Title Example\n\n"
                "## 1. アブストラクト\n\n"
                "要約本文。\n\n"
                "---\n",
                encoding="utf-8",
            )
            for name in [
                "chapter1-introduction.md",
                "chapter2-theoretical-framework.md",
                "chapter3-core-mechanisms.md",
                "chapter4-case-study.md",
                "chapter5-limitations-ethics.md",
                "chapter6-conclusion.md",
            ]:
                (paper / "chapters" / name).write_text(
                    f"# {name}\n\n本文。\n", encoding="utf-8"
                )
            (paper / "chapters" / "references.md").write_text(
                "## 参考文献\n\n- Yin, R. K. (2018).\n", encoding="utf-8"
            )
            for name in [
                "appendix-a-glossary.md",
                "appendix-b-dialogue-excerpt.md",
                "appendix-c-audit-index.md",
            ]:
                (paper / "manuscript" / name).write_text(
                    f"## {name}\n\n付録。\n", encoding="utf-8"
                )

            from assemble_manuscript import main

            rc = main(["cognitive-scaffolding", "--repo-root", str(root)])
            self.assertEqual(rc, 0)
            expected = paper / "manuscript" / "正式タイトル例：副題.md"
            self.assertTrue(expected.is_file(), f"missing {expected}")
            self.assertFalse(
                (paper / "manuscript" / "cognitive-scaffolding-draft.md").exists()
            )

    def _make_fixture(self, root: Path, chapter_body: str) -> Path:
        paper = root / "docs" / "cognitive-scaffolding"
        (paper / "design" / "sot").mkdir(parents=True)
        (paper / "chapters").mkdir(parents=True)
        (paper / "manuscript").mkdir(parents=True)
        (paper / "design" / "sot" / "paper-outline.md").write_text(
            "**論文仮題（和文）**: 正式タイトル例：副題\n"
            "**論文仮題（英文）**: Official Title Example\n\n"
            "## 1. アブストラクト\n\n"
            "要約本文。\n\n"
            "---\n",
            encoding="utf-8",
        )
        for name in [
            "chapter1-introduction.md",
            "chapter2-theoretical-framework.md",
            "chapter3-core-mechanisms.md",
            "chapter4-case-study.md",
            "chapter5-limitations-ethics.md",
            "chapter6-conclusion.md",
        ]:
            (paper / "chapters" / name).write_text(
                f"# {name}\n\n本文。\n", encoding="utf-8"
            )
        (paper / "chapters" / "chapter4-case-study.md").write_text(
            chapter_body, encoding="utf-8"
        )
        (paper / "chapters" / "references.md").write_text(
            "## 参考文献\n\n- Yin, R. K. (2018).\n", encoding="utf-8"
        )
        for name in [
            "appendix-a-glossary.md",
            "appendix-b-dialogue-excerpt.md",
            "appendix-c-audit-index.md",
        ]:
            (paper / "manuscript" / name).write_text(
                f"## {name}\n\n付録。\n", encoding="utf-8"
            )
        return paper

    def test_assembly_blocked_on_readability_fail(self):
        """Fail-stop: prose carrying bare internal codes must block assembly."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paper = self._make_fixture(root, "# 章\n\nNC-09 は主語として不可。\n")

            from assemble_manuscript import main

            rc = main(["cognitive-scaffolding", "--repo-root", str(root)])
            self.assertEqual(rc, 1)
            self.assertFalse(
                (paper / "manuscript" / "正式タイトル例：副題.md").exists()
            )

            rc = main(["cognitive-scaffolding", "--repo-root", str(root), "--force"])
            self.assertEqual(rc, 0)
            self.assertTrue(
                (paper / "manuscript" / "正式タイトル例：副題.md").is_file()
            )

    def test_discovers_non_scaffolding_chapter_names_without_appendices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paper = root / "docs" / "jiatama-supremacism"
            (paper / "design" / "sot").mkdir(parents=True)
            (paper / "chapters").mkdir(parents=True)
            (paper / "manuscript").mkdir(parents=True)
            (paper / "design" / "sot" / "paper-outline.md").write_text(
                "**論文仮題（和文）**: 正式タイトル例：副題\n"
                "**論文仮題（英文）**: Official Title Example\n"
                "**著者**: 小越 秀\n"
                "**所属**: なし（独立研究者）\n"
                "**日付**: 2026-08-22\n"
                "**ライセンス**: CC BY 4.0\n"
                "**バージョン**: v1.0.0\n\n"
                "## 1. アブストラクト\n\n"
                "要約本文。\n\n"
                "---\n",
                encoding="utf-8",
            )
            for name in [
                "chapter1-introduction.md",
                "chapter2-genealogy-i.md",
                "chapter3-genealogy-ii.md",
                "chapter4-self-undermining.md",
                "chapter5-resistance.md",
                "chapter6-conclusion.md",
            ]:
                (paper / "chapters" / name).write_text(
                    f"# {name}\n\n本文。\n", encoding="utf-8"
                )
            (paper / "chapters" / "references.md").write_text(
                "## 参考文献\n\n- Blair, A. (2003).\n", encoding="utf-8"
            )

            from assemble_manuscript import main

            rc = main(["jiatama-supremacism", "--repo-root", str(root)])
            self.assertEqual(rc, 0)
            out = (paper / "manuscript" / "正式タイトル例：副題.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("chapter2-genealogy-i.md", out)
            self.assertIn("- **著者**: 小越 秀", out)
            self.assertIn("- **バージョン**: v1.0.0", out)
            self.assertNotIn("# 付録", out)
            self.assertNotIn("Yin (2018)", out)


if __name__ == "__main__":
    unittest.main()
