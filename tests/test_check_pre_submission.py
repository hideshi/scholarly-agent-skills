#!/usr/bin/env python3
"""Unit tests for check_pre_submission.py (stdlib only)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from check_pre_submission import main  # noqa: E402


def write_minimal_paper(root: Path) -> None:
    base = root / "docs" / "cognitive-scaffolding"
    (base / "chapters").mkdir(parents=True)
    (base / "literature" / "papers").mkdir(parents=True)
    (base / "literature" / "literature-matrix.md").write_text(
        "| DOI/URL | 文献名 | 著者 | 年 | 方法 | 知見 | テーマ | 評価 |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| [x](https://example.com) | T | Smith, J. | 2020 | M | F | Th | ★ |\n",
        encoding="utf-8",
    )
    (base / "literature" / "papers" / "smith-2020.md").write_text(
        "---\n"
        "title: T\n"
        "authors: Smith, J.\n"
        "year: 2020\n"
        "status: full-text\n"
        "---\n\n"
        + ("Full text body. " * 200),
        encoding="utf-8",
    )
    (base / "chapters" / "chapter1-introduction.md").write_text(
        "# 序論\n\nSmith (2020) によると、〜である。\n",
        encoding="utf-8",
    )


class TestCheckPreSubmission(unittest.TestCase):
    def test_gate_passes_on_minimal_grounded_paper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_minimal_paper(root)
            rc = main(["cognitive-scaffolding", "--repo-root", str(root)])
            self.assertEqual(rc, 0)

    def test_gate_fails_when_chapters_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc = main(["cognitive-scaffolding", "--repo-root", tmp])
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
