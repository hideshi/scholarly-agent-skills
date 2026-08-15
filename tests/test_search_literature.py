#!/usr/bin/env python3
"""
Unit tests for search_literature.py multi-provider literature search engine.
Uses ONLY Python standard library.
"""

import sys
import os
import unittest
import tempfile
import json
from unittest.mock import patch
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from search_literature import (
    search_literature,
    format_markdown,
    load_config,
    build_user_agent,
)
from contact_email import ContactEmailError


SAMPLE_OPENALEX_JSON = {
    "results": [
        {
            "id": "https://openalex.org/W123456789",
            "title": "Hermeneutic Analysis of Open Access Literature",
            "publication_year": 2023,
            "authorships": [
                {"author": {"display_name": "Dr. Clara Oswald"}}
            ],
            "abstract_inverted_index": {
                "This": [0],
                "is": [1],
                "a": [2],
                "test": [3],
                "abstract.": [4]
            },
            "doi": "https://doi.org/10.1234/test.2023"
        }
    ]
}


class TestSearchLiterature(unittest.TestCase):

    def test_build_user_agent_includes_mailto_when_set(self):
        self.assertEqual(build_user_agent(""), "Scholarly-Agent-Skills/1.0")
        self.assertEqual(
            build_user_agent("firstname.lastname@university.ac.jp"),
            "Scholarly-Agent-Skills/1.0 (mailto:firstname.lastname@university.ac.jp)",
        )

    def test_search_literature_stops_without_usable_email(self):
        env_without_contact = {
            key: value for key, value in os.environ.items() if key != "SCHOLARLY_CONTACT_EMAIL"
        }
        with patch.dict(os.environ, env_without_contact, clear=True):
            with self.assertRaises(ContactEmailError) as ctx:
                search_literature("hermeneutics", provider_key="openalex", max_results=1)
            self.assertIn("export SCHOLARLY_CONTACT_EMAIL=", str(ctx.exception))

    def test_load_config_fallback(self):
        config = load_config(Path("/nonexistent/path/config.json"))
        self.assertIn("providers", config)
        self.assertIn("arxiv", config["providers"])
        self.assertIn("openalex", config["providers"])

    @patch("search_literature.fetch_url")
    def test_search_openalex_provider(self, mock_fetch):
        mock_fetch.return_value = json.dumps(SAMPLE_OPENALEX_JSON).encode("utf-8")

        with patch.dict(os.environ, {"SCHOLARLY_CONTACT_EMAIL": "firstname.lastname@university.ac.jp"}):
            results = search_literature("hermeneutics", provider_key="openalex", max_results=1)
        self.assertEqual(len(results), 1)
        paper = results[0]
        self.assertEqual(paper["provider"], "OpenAlex")
        self.assertEqual(paper["id"], "W123456789")
        self.assertEqual(paper["title"], "Hermeneutic Analysis of Open Access Literature")
        self.assertEqual(paper["authors"], ["Dr. Clara Oswald"])
        self.assertEqual(paper["published"], "2023")
        self.assertEqual(paper["summary"], "This is a test abstract.")
        self.assertEqual(paper["url"], "https://doi.org/10.1234/test.2023")

    def test_format_markdown_multi_provider(self):
        papers = [
            {
                "provider": "OpenAlex",
                "id": "W123456789",
                "title": "Sample Paper",
                "authors": ["Author One"],
                "published": "2023",
                "summary": "Sample summary text.",
                "url": "https://doi.org/10.1234/sample"
            }
        ]
        markdown = format_markdown(papers)
        self.assertIn("# Multi-Provider Literature Search Results", markdown)
        self.assertIn("`OpenAlex`", markdown)
        self.assertIn("[Sample Paper](https://doi.org/10.1234/sample)", markdown)

    def test_custom_config_loading(self):
        custom_config = {
            "default_provider": "custom_api",
            "providers": {
                "custom_api": {
                    "name": "Custom Provider",
                    "type": "openalex_json",
                    "base_url": "https://api.example.com/works",
                    "enabled": True
                }
            }
        }
        with tempfile.NamedTemporaryFile("w+", suffix=".json", encoding="utf-8", delete=False) as tmp:
            json.dump(custom_config, tmp)
            tmp_path = Path(tmp.name)

        try:
            config = load_config(tmp_path)
            self.assertEqual(config["default_provider"], "custom_api")
            self.assertIn("custom_api", config["providers"])
        finally:
            tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
