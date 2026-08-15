#!/usr/bin/env python3
"""
Unit tests for fetch_macro_data.py using ONLY Python standard library.
"""

import sys
import unittest
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from fetch_macro_data import (
    format_as_markdown,
    format_as_csv,
    PRESETS
)


class TestFetchMacroData(unittest.TestCase):

    def test_presets_exist(self):
        self.assertIn("poverty", PRESETS)
        self.assertIn("macro", PRESETS)
        self.assertIn("SI.POV.GINI", PRESETS["poverty"])

    def test_format_as_markdown(self):
        sample_data = {
            "2020": {"Year": "2020", "GDP Growth": 5.4, "Gini Index": 42.3},
            "2021": {"Year": "2021", "GDP Growth": -9.5, "Gini Index": None}
        }
        labels = ["GDP Growth", "Gini Index"]
        md_table = format_as_markdown(sample_data, labels, "PH", 2020, 2021)
        
        self.assertIn("<!-- Source: World Bank Open Data API", md_table)
        self.assertIn("| Year | GDP Growth | Gini Index |", md_table)
        self.assertIn("| 2020 | 5.40 | 42.30 |", md_table)
        self.assertIn("| 2021 | -9.50 | N/A |", md_table)

    def test_format_as_csv(self):
        sample_data = {
            "2020": {"Year": "2020", "GDP Growth": 5.4, "Gini Index": 42.3},
            "2021": {"Year": "2021", "GDP Growth": -9.5, "Gini Index": None}
        }
        labels = ["GDP Growth", "Gini Index"]
        csv_str = format_as_csv(sample_data, labels)
        
        self.assertIn("Year,GDP Growth,Gini Index", csv_str)
        self.assertIn("2020,5.4,42.3", csv_str)
        self.assertIn("2021,-9.5,", csv_str)


if __name__ == "__main__":
    unittest.main()
