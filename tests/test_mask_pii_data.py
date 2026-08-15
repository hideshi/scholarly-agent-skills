#!/usr/bin/env python3
"""
Unit tests for mask_pii_data.py using ONLY Python standard library.
"""

import sys
import unittest
import tempfile
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from mask_pii_data import mask_pii_text, anonymize_file, load_name_mapping_file


class TestMaskPiiData(unittest.TestCase):

    def test_load_name_mapping_file_json_and_text(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_file = Path(tmp_dir) / "mapping.json"
            json_file.write_text('{"山田太郎": "調査対象者A", "佐藤花子": "調査対象者B"}', encoding="utf-8")

            mapping_json = load_name_mapping_file(json_file)
            self.assertEqual(mapping_json.get("山田太郎"), "調査対象者A")
            self.assertEqual(mapping_json.get("佐藤花子"), "調査対象者B")

            text_file = Path(tmp_dir) / "mapping.txt"
            text_file.write_text("John Doe=Participant_A\nJane Smith=Participant_B", encoding="utf-8")

            mapping_text = load_name_mapping_file(text_file)
            self.assertEqual(mapping_text.get("John Doe"), "Participant_A")
            self.assertEqual(mapping_text.get("Jane Smith"), "Participant_B")

    def test_mask_pii_text_email_phone_postal(self):
        raw = "Contact Alice at alice@example.com or 090-1234-5678, postal code 〒123-4567."
        masked = mask_pii_text(raw, name_replacements={"Alice": "Participant_A"})

        self.assertIn("Participant_A", masked)
        self.assertNotIn("alice@example.com", masked)
        self.assertIn("[EMAIL_MASKED]", masked)
        self.assertNotIn("090-1234-5678", masked)
        self.assertIn("[PHONE_MASKED]", masked)
        self.assertNotIn("〒123-4567", masked)
        self.assertIn("[POSTAL_MASKED]", masked)

    def test_honorific_name_masking_jp_and_en(self):
        text = "山田教授と佐藤代表が会議に参加。Dr. Watson and Prof. John Davis attended."
        masked = mask_pii_text(text, auto_mask_honorifics=True)

        self.assertNotIn("山田教授", masked)
        self.assertIn("[NAME_MASKED]教授", masked)
        self.assertNotIn("佐藤代表", masked)
        self.assertIn("[NAME_MASKED]代表", masked)

        self.assertNotIn("Dr. Watson", masked)
        self.assertIn("Dr. [NAME_MASKED]", masked)
        self.assertNotIn("Prof. John Davis", masked)
        self.assertIn("Prof. [NAME_MASKED]", masked)

    def test_anonymize_file_pipeline(self):
        content = "Interview with Bob (bob@research.org). Tel: 03-9999-8888."
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = Path(tmp_dir) / "raw_interview.txt"
            input_file.write_text(content, encoding="utf-8")

            out_file = anonymize_file(input_file, name_replacements={"Bob": "Respondent_1"})
            self.assertTrue(out_file.exists())

            anonymized_text = out_file.read_text(encoding="utf-8")
            self.assertIn("Respondent_1", anonymized_text)
            self.assertIn("[EMAIL_MASKED]", anonymized_text)
            self.assertIn("[PHONE_MASKED]", anonymized_text)


if __name__ == "__main__":
    unittest.main()
