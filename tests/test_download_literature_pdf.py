#!/usr/bin/env python3
"""Unit tests for download_literature_pdf.py (stdlib + mocks only)."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from download_literature_pdf import (
    download_pdf_url,
    format_human_handoff,
    infer_referer,
    is_bot_challenge_html,
    is_valid_pdf_bytes,
    needs_human_handoff,
    normalize_doi,
    parse_frontmatter,
    resolve_pdf_candidates,
)


class TestDownloadLiteraturePdf(unittest.TestCase):
    def test_normalize_doi(self):
        self.assertEqual(normalize_doi("https://doi.org/10.1007/s00146-010-0272-8"), "10.1007/s00146-010-0272-8")

    def test_infer_referer_springer(self):
        url = "https://link.springer.com/content/pdf/10.1007/s00146-010-0272-8.pdf"
        self.assertEqual(
            infer_referer(url),
            "https://link.springer.com/article/10.1007/s00146-010-0272-8",
        )

    def test_infer_referer_wiley(self):
        url = "https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/j.1469-7610.1976.tb00381.x"
        self.assertEqual(
            infer_referer(url),
            "https://onlinelibrary.wiley.com/doi/10.1111/j.1469-7610.1976.tb00381.x",
        )

    def test_is_valid_pdf_bytes(self):
        self.assertTrue(is_valid_pdf_bytes(b"%PDF-1.4\n" + b"x" * 2000))
        self.assertFalse(is_valid_pdf_bytes(b"<html>error</html>"))
        self.assertFalse(is_valid_pdf_bytes(b"%PDF tiny"))

    def test_is_bot_challenge_html(self):
        cloudflare = b"<!doctype html><html><title>Just a moment...</title></html>"
        recaptcha = b"<html><div class='g-recaptcha'></div></html>"
        self.assertTrue(is_bot_challenge_html(cloudflare))
        self.assertTrue(is_bot_challenge_html(recaptcha))
        self.assertFalse(is_bot_challenge_html(b"%PDF-1.4\n"))
        self.assertFalse(is_bot_challenge_html(b"<html><body>404 Not Found</body></html>"))

    def test_needs_human_handoff(self):
        self.assertTrue(needs_human_handoff("bot-challenge (reCAPTCHA/Cloudflare): human handoff required"))
        self.assertFalse(needs_human_handoff("HTTP 404"))

    def test_format_human_handoff(self):
        msg = format_human_handoff("wood-1976", "https://doi.org/10.1111/example")
        self.assertIn("wood-1976.pdf", msg)
        self.assertIn("https://doi.org/10.1111/example", msg)

    def test_parse_frontmatter(self):
        text = '---\ntitle: "Test"\ndoi: 10.1234/test\nstatus: abstract-only\n---\n\n# Body\n'
        meta = parse_frontmatter(text)
        self.assertEqual(meta["doi"], "10.1234/test")
        self.assertEqual(meta["status"], "abstract-only")

    @patch("download_literature_pdf.fetch_json")
    def test_resolve_pdf_candidates_openalex_and_s2(self, mock_fetch):
        def side_effect(url, headers):
            if "openalex.org" in url:
                return {
                    "best_oa_location": {"pdf_url": "https://example.org/paper.pdf"},
                    "locations": [{"pdf_url": "https://example.org/alt.pdf"}],
                }
            return {"openAccessPdf": {"url": "https://example.org/s2.pdf"}}
        mock_fetch.side_effect = side_effect

        with patch.dict("os.environ", {"SCHOLARLY_CONTACT_EMAIL": "researcher@university.ac.jp"}):
            from search_literature import build_request_headers

            candidates = resolve_pdf_candidates("10.1234/test", build_request_headers("researcher@university.ac.jp"))

        labels = [c[0] for c in candidates]
        self.assertIn("openalex:best", labels)
        self.assertIn("semanticscholar", labels)
        urls = {c[1] for c in candidates}
        self.assertIn("https://example.org/paper.pdf", urls)

    def test_download_pdf_url_writes_valid_pdf(self):
        pdf_bytes = b"%PDF-1.4\n" + b"0" * 3000
        import io
        import urllib.request

        class FakeResponse:
            def __init__(self, data):
                self._data = data

            def read(self):
                return self._data

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        with patch("urllib.request.urlopen", return_value=FakeResponse(pdf_bytes)):
            import tempfile

            with tempfile.TemporaryDirectory() as tmp:
                dest = Path(tmp) / "test.pdf"
                ok, msg = download_pdf_url("https://example.org/x.pdf", dest, {"User-Agent": "test"})
                self.assertTrue(ok)
                self.assertTrue(dest.exists())
                self.assertTrue(is_valid_pdf_bytes(dest.read_bytes()))

    def test_download_pdf_url_rejects_captcha_html(self):
        html = b"<!doctype html><html><title>Just a moment...</title><body>cf-turnstile</body></html>"
        import tempfile
        import urllib.request

        class FakeResponse:
            def __init__(self, data):
                self._data = data

            def read(self):
                return self._data

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        with patch("urllib.request.urlopen", return_value=FakeResponse(html)):
            with tempfile.TemporaryDirectory() as tmp:
                dest = Path(tmp) / "test.pdf"
                ok, msg = download_pdf_url("https://example.org/x.pdf", dest, {"User-Agent": "test"})
                self.assertFalse(ok)
                self.assertIn("bot-challenge", msg)
                self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main()
