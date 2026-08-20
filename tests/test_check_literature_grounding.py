#!/usr/bin/env python3
"""Unit tests for check_literature_grounding.py (stdlib only)."""

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from check_literature_grounding import (  # noqa: E402
    audit_grounding,
    classify_paper,
    load_paper_records,
    parse_frontmatter,
    PaperRecord,
)


class TestFrontmatter(unittest.TestCase):
    def test_parse_frontmatter(self):
        text = "---\ntitle: Test\nauthors: Smith, J.\nyear: 2020\nstatus: full-text\n---\n\nBody text here."
        meta, body = parse_frontmatter(text)
        self.assertEqual(meta["title"], "Test")
        self.assertEqual(meta["year"], "2020")
        self.assertIn("Body text", body)


class TestClassifyPaper(unittest.TestCase):
    def test_fail_when_missing(self):
        verdict, _ = classify_paper(None)
        self.assertEqual(verdict, "FAIL")

    def test_pass_full_text_with_pdf(self):
        paper = PaperRecord(
            path=Path("x.md"),
            title="T",
            authors="Risko",
            year="2016",
            doi="",
            arxiv_id="",
            status="full-text",
            body_chars=1000,
            source_pdf=Path("_downloads/x.pdf"),
        )
        verdict, _ = classify_paper(paper)
        self.assertEqual(verdict, "PASS")

    def test_warn_full_text_without_pdf(self):
        paper = PaperRecord(
            path=Path("gakushuin-exam-misconduct.md"),
            title="T",
            authors="Gakushuin",
            year="2023",
            doi="",
            arxiv_id="",
            status="full-text",
            body_chars=1000,
        )
        verdict, reason = classify_paper(paper)
        self.assertEqual(verdict, "WARN")
        self.assertIn("_downloads/gakushuin-exam-misconduct.pdf", reason)

    def test_warn_manual_stub(self):
        paper = PaperRecord(
            path=Path("x.md"),
            title="T",
            authors="Barkley",
            year="2012",
            doi="",
            arxiv_id="",
            status="manual-stub",
            body_chars=200,
        )
        verdict, _ = classify_paper(paper)
        self.assertEqual(verdict, "WARN")


class TestAuditGrounding(unittest.TestCase):
    def test_audit_finds_fail_without_papers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chapters = root / "chapters"
            papers = root / "papers"
            chapters.mkdir()
            papers.mkdir()
            chapter = chapters / "ch1.md"
            chapter.write_text(
                "Prior work shows an effect (Risko & Gilbert, 2016).\n",
                encoding="utf-8",
            )
            results = audit_grounding([chapter], papers, None)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].verdict, "FAIL")

    def test_audit_pass_with_matching_paper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chapters = root / "chapters"
            papers = root / "papers"
            chapters.mkdir()
            papers.mkdir()
            chapter = chapters / "ch1.md"
            chapter.write_text(
                "Prior work shows an effect (Risko & Gilbert, 2016).\n",
                encoding="utf-8",
            )
            paper = papers / "risko-2016.md"
            body = "x" * 600
            paper.write_text(
                "---\ntitle: Cognitive Offloading\nauthors: Risko, E. F., & Gilbert, S. J.\n"
                "year: 2016\nstatus: full-text\ndoi: \narxiv_id: \n---\n\n" + body,
                encoding="utf-8",
            )
            (papers / "_downloads").mkdir()
            (papers / "_downloads" / "risko-2016.pdf").write_bytes(b"%PDF-1.4\n" + b"x" * 64)
            results = audit_grounding([chapter], papers, None)
            self.assertEqual(results[0].verdict, "PASS")

    def test_audit_warns_full_text_without_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chapters = root / "chapters"
            papers = root / "papers"
            chapters.mkdir()
            papers.mkdir()
            chapter = chapters / "ch1.md"
            chapter.write_text(
                "Prior work shows an effect (Risko & Gilbert, 2016).\n",
                encoding="utf-8",
            )
            paper = papers / "risko-2016.md"
            body = "x" * 600
            paper.write_text(
                "---\ntitle: Cognitive Offloading\nauthors: Risko, E. F., & Gilbert, S. J.\n"
                "year: 2016\nstatus: full-text\ndoi: \narxiv_id: \n---\n\n" + body,
                encoding="utf-8",
            )
            results = audit_grounding([chapter], papers, None)
            self.assertEqual(results[0].verdict, "WARN")
            self.assertIn("_downloads/risko-2016.pdf", results[0].reason)

    def test_load_skips_underscore_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            papers = Path(tmp)
            (papers / "_ingestion-log.md").write_text("---\ntitle: log\n---\n", encoding="utf-8")
            (papers / "real.md").write_text(
                "---\ntitle: Real\nauthors: A\nyear: 2020\nstatus: full-text\n---\n" + ("b" * 600),
                encoding="utf-8",
            )
            records = load_paper_records(papers)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].title, "Real")


if __name__ == "__main__":
    unittest.main()
