#!/usr/bin/env python3
"""
Unit tests for evaluate_source_trust.py using ONLY Python standard library.
Tests Default-Deny policy, strict domain matching, and adversarial bypass attempts.
"""

import sys
import unittest
import tempfile
import json
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from evaluate_source_trust import evaluate_source, extract_hostname, domain_matches


class TestEvaluateSourceTrust(unittest.TestCase):

    def test_extract_hostname(self):
        self.assertEqual(extract_hostname("https://openknowledge.worldbank.org/handle/10986"), "openknowledge.worldbank.org")
        self.assertEqual(extract_hostname("http://user:pass@arxiv.org:8080/abs/1234"), "arxiv.org")
        self.assertEqual(extract_hostname("psa.gov.ph"), "psa.gov.ph")

    def test_domain_matches(self):
        self.assertTrue(domain_matches("arxiv.org", "arxiv.org"))
        self.assertTrue(domain_matches("sub.arxiv.org", "arxiv.org"))
        self.assertFalse(domain_matches("arxiv.org.evil.com", "arxiv.org"))
        self.assertFalse(domain_matches("notarxiv.org", "arxiv.org"))
        self.assertTrue(domain_matches("dswd.gov.ph", ".gov.ph"))
        self.assertFalse(domain_matches("evilgov", ".gov"))

    def test_tier_1_standard_domains(self):
        urls = [
            "https://openknowledge.worldbank.org/handle/10986/12345",
            "https://arxiv.org/abs/2607.29189",
            "https://psa.gov.ph/content/poverty-statistics",
            "https://repec.org/paper.html"
        ]
        for u in urls:
            tier, label, _ = evaluate_source(u)
            self.assertEqual(tier, 1, f"Expected Tier 1 for {u}, got Tier {tier}")
            self.assertIn("APPROVED", label)

    def test_tier_2_standard_domains(self):
        urls = [
            "https://www.pids.gov.ph/publication/pids-study",
            "https://dswd.gov.ph/reports",
            "https://university.edu/paper.pdf",
            "https://research.ac.jp/paper"
        ]
        for u in urls:
            tier, label, _ = evaluate_source(u)
            self.assertEqual(tier, 2, f"Expected Tier 2 for {u}, got Tier {tier}")
            self.assertIn("ACCEPTABLE", label)

    def test_adversarial_bypass_attempts(self):
        evil_urls = [
            "https://arxiv.org.evil.com/fake-paper",     # Suffix forgery
            "https://notarxiv.org/abs/1234",             # Label boundary missing
            "https://fake.gov.phishing.com/report",      # .gov. middle match
            "http://evil.com@arxiv.org/",                # Userinfo spoofing
            "https://psa.gov.ph.attacker.net/",          # gov.ph forgery
            "https://evilgov.com/fake",                  # Loose "gov" suffix
            "https://myedu.net/fake"                     # Loose "edu" suffix
        ]
        for u in evil_urls:
            tier, label, _ = evaluate_source(u)
            self.assertEqual(tier, 3, f"BYPASS VULNERABILITY DETECTED: {u} was approved as Tier {tier} ({label})")

    def test_custom_trusted_domains_config(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "trusted_domains.json"
            config_data = {
                "tier_1": ["my-custom-journal.org"],
                "tier_2": ["my-local-thinktank.org"]
            }
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            # Custom Tier 1 test
            t1_url = "https://sub.my-custom-journal.org/paper"
            tier, label, _ = evaluate_source(t1_url, config_path=config_path)
            self.assertEqual(tier, 1)

            # Custom Tier 2 test
            t2_url = "https://my-local-thinktank.org/report"
            tier, label, _ = evaluate_source(t2_url, config_path=config_path)
            self.assertEqual(tier, 2)


if __name__ == "__main__":
    unittest.main()
