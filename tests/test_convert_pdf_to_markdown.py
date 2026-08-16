#!/usr/bin/env python3
"""
Unit tests for convert_pdf_to_markdown.py using ONLY Python standard library.
"""

import sys
import unittest
import tempfile
import zlib
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from convert_pdf_to_markdown import (
    unescape_pdf_string,
    parse_pdf_text_operators,
    extract_images_from_pdf_stream,
    convert_pdf_to_markdown,
    normalize_ppm_images,
    convert_ppm_to_png,
)


class TestConvertPdfToMarkdown(unittest.TestCase):

    def test_unescape_pdf_string(self):
        escaped = r"Hello \(World\) \\ Test"
        expected = "Hello (World) \\ Test"
        self.assertEqual(unescape_pdf_string(escaped), expected)

    def test_parse_pdf_text_operators(self):
        stream_content = b"BT /F1 12 Tf (Hello PDF World) Tj ET"
        text = parse_pdf_text_operators(stream_content)
        self.assertIn("Hello PDF World", text)

    def test_extract_jpeg_image_from_pdf_stream(self):
        # Construct synthetic PDF stream containing a JPEG image
        jpeg_header = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xd9"
        pdf_stream = (
            b"1 0 obj\n"
            b"<< /Type /XObject /Subtype /Image /Width 10 /Height 10 /Filter /DCTDecode >>\n"
            b"stream\n" + jpeg_header + b"\nendstream\n"
            b"endobj\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            assets_dir = Path(tmp_dir) / "assets"
            saved_images = extract_images_from_pdf_stream(pdf_stream, assets_dir)
            
            self.assertEqual(len(saved_images), 1)
            self.assertEqual(saved_images[0], "extracted_image_1.jpg")
            self.assertTrue((assets_dir / "extracted_image_1.jpg").exists())
            self.assertEqual((assets_dir / "extracted_image_1.jpg").read_bytes(), jpeg_header)

    def test_convert_pdf_to_markdown_full_pipeline(self):
        # Construct synthetic PDF with text and JPEG image
        decompressed_text = b"BT /F1 12 Tf (Introduction to Philosophy) Tj ET"
        compressed_text = zlib.compress(decompressed_text)
        jpeg_data = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xd9"
        
        pdf_content = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Filter /FlateDecode >>\nstream\n" + compressed_text + b"\nendstream\nendobj\n"
            b"2 0 obj\n<< /Subtype /Image /Filter /DCTDecode >>\nstream\n" + jpeg_data + b"\nendstream\nendobj\n"
            b"%%EOF\n"
        )
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "sample_paper.pdf"
            pdf_path.write_bytes(pdf_content)
            
            md_path, images = convert_pdf_to_markdown(pdf_path, output_dir=Path(tmp_dir))
            
            self.assertTrue(md_path.exists())
            self.assertEqual(len(images), 1)
            
            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("# Sample Paper", md_text)
            self.assertIn("Introduction to Philosophy", md_text)
            self.assertIn("![extracted_image_1.jpg](assets/extracted_image_1.jpg)", md_text)

    def test_convert_ppm_to_png_when_pillow_available(self):
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            self.skipTest("Pillow not installed")

        with tempfile.TemporaryDirectory() as tmp_dir:
            ppm_path = Path(tmp_dir) / "sample.ppm"
            # Minimal P5 grayscale 2x2 image
            ppm_path.write_bytes(b"P5\n2 2\n255\n\x00\xFF\x80\x40")
            png_path = convert_ppm_to_png(ppm_path)
            self.assertIsNotNone(png_path)
            self.assertTrue(png_path.exists())
            self.assertEqual(png_path.suffix, ".png")

    def test_normalize_ppm_images_replaces_names(self):
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            self.skipTest("Pillow not installed")

        with tempfile.TemporaryDirectory() as tmp_dir:
            assets_dir = Path(tmp_dir)
            ppm_path = assets_dir / "extracted_image_1.ppm"
            ppm_path.write_bytes(b"P5\n1 1\n255\n\x80")
            names = normalize_ppm_images(assets_dir, ["extracted_image_1.ppm", "extracted_image_2.jpg"])
            self.assertEqual(names[0], "extracted_image_1.png")
            self.assertFalse(ppm_path.exists())
            self.assertTrue((assets_dir / "extracted_image_1.png").exists())
            self.assertEqual(names[1], "extracted_image_2.jpg")


if __name__ == "__main__":
    unittest.main()
