#!/usr/bin/env python3
"""
Unit tests for convert_markdown_to_pdf.py using ONLY Python standard library.
"""

import sys
import unittest
import tempfile
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from convert_markdown_to_pdf import convert_md_to_pdf, ACADEMIC_CSS, render_markdown_body


class TestConvertMarkdownToPdf(unittest.TestCase):

    def test_academic_css_contains_paper_styles(self):
        self.assertIn("@page", ACADEMIC_CSS)
        self.assertIn("A4", ACADEMIC_CSS)
        self.assertIn("Times New Roman", ACADEMIC_CSS)

    def test_render_markdown_body_converts_headers(self):
        md_sample = "# Heading 1\n\nSome paragraph text."
        rendered = render_markdown_body(md_sample)
        # Should be converted to HTML or wrapped cleanly in pre
        self.assertTrue("<h1" in rendered or "<pre>" in rendered)
        self.assertNotIn("# Heading 1", rendered if "<h1" in rendered else "")

    def test_render_keeps_list_after_fullwidth_colon(self):
        md_sample = (
            "具体的には、以下を担う：\n"
            "- **自由度の縮小**: foo\n"
            "- **方向維持**: bar\n"
        )
        rendered = render_markdown_body(md_sample)
        self.assertIn("<ul>", rendered)
        self.assertIn("<li>", rendered)
        self.assertNotIn("：\n- ", rendered)
        self.assertNotRegex(rendered, r"<p>[^<]*：\s*-")

    def test_replace_mermaid_blocks_with_images(self):
        from convert_markdown_to_pdf import replace_mermaid_blocks_with_images

        md_sample = (
            "図を示す。\n\n"
            "```mermaid\n"
            "flowchart TD\n"
            "  A --> B\n"
            "```\n\n"
            "以上。\n"
        )
        out = replace_mermaid_blocks_with_images(md_sample)
        if "data:image/png;base64," in out:
            self.assertIn('class="mermaid-figure"', out)
            self.assertNotIn("```mermaid", out)
        else:
            # mermaid-cli unavailable in CI: leave fence intact
            self.assertIn("```mermaid", out)

    def test_convert_md_to_pdf_creates_output(self):
        sample_md = (
            "# Academic Paper Title\n\n"
            "## Abstract\n\n"
            "This is a test abstract for the academic paper.\n\n"
            "## 1. Introduction\n\n"
            "This is the introduction paragraph with **bold** text and `code`.\n"
        )
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_md = Path(tmp_dir) / "sample_paper.md"
            input_md.write_text(sample_md, encoding="utf-8")
            
            output_pdf = Path(tmp_dir) / "sample_paper.pdf"
            
            is_pdf, kind = convert_md_to_pdf(input_md, output_pdf)
            self.assertIn(kind, ["pdf", "html"])
            
            output_html = output_pdf.with_suffix(".html")
            self.assertTrue(output_html.exists() or output_pdf.exists())
            
            if output_html.exists():
                html_text = output_html.read_text(encoding="utf-8")
                self.assertIn("Academic Paper Title", html_text)


if __name__ == "__main__":
    unittest.main()
