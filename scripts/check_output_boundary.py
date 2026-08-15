#!/usr/bin/env python3
"""
Output Boundary Enforcement Script for Academic Papers.
Scans manuscript Markdown files (e.g. in docs/chapters/) to ensure no internal
engineering or process workflow labels (TDD, Red, Green, Refactor, Phase, Test Case, etc.)
leak into the published manuscript text.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

FORBIDDEN_PATTERN = re.compile(
    r'\b(TDD|Red\s*Phase|Green\s*Phase|Refactor|Test[- ]?Case|Sprint|Coverage)\b|'
    r'テストケース|フェーズ\s*\d|スプリント|カバレッジ|リファクタ|'
    r'docs/data/|docs/literature/|docs/design/|一次データ:\s*docs/|data:\s*docs/',
    re.IGNORECASE
)


def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Scans a single Markdown file for forbidden internal workflow terms.
    Returns list of (line_number, matched_text, line_snippet).
    """
    violations = []
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}", file=sys.stderr)
        return violations

    for line_idx, line in enumerate(content.splitlines(), start=1):
        match = FORBIDDEN_PATTERN.search(line)
        if match:
            violations.append((line_idx, match.group(0), line.strip()[:80]))

    return violations


def scan_target(target_path: Path) -> List[Tuple[Path, int, str, str]]:
    """
    Scans a file or directory recursively for manuscript boundary violations.
    Excludes design documents (e.g. test-cases.md).
    """
    all_violations = []
    if target_path.is_file():
        files = [target_path]
    elif target_path.is_dir():
        files = [f for f in target_path.rglob("*.md") if f.name not in ("test-cases.md", "evidence-gate-report.md", "references.md")]
    else:
        print(f"❌ Error: Target path '{target_path}' does not exist.", file=sys.stderr)
        return all_violations

    for file_path in sorted(files):
        file_violations = scan_file(file_path)
        for line_num, match_str, snippet in file_violations:
            all_violations.append((file_path, line_num, match_str, snippet))

    return all_violations


def main():
    parser = argparse.ArgumentParser(description="Check manuscript Markdown files for forbidden internal workflow terms.")
    parser.add_argument("target", nargs="?", default="docs/chapters", help="Target manuscript directory or Markdown file to scan (default: docs/chapters)")
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    print(f"🔍 Scanning manuscript path for Output Boundary compliance: {target_path}")

    violations = scan_target(target_path)

    if not violations:
        print("✅ Output Boundary Check PASSED: No internal workflow terms detected in manuscript files.")
        sys.exit(0)

    print(f"💥 Output Boundary Check FAILED: Found {len(violations)} violation(s):\n", file=sys.stderr)
    for file_path, line_num, match_str, snippet in violations:
        print(f"  ❌ {file_path.name}:{line_num} -> Term '{match_str}' found in line: '{snippet}'", file=sys.stderr)

    sys.exit(1)


if __name__ == '__main__':
    main()
