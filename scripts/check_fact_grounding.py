#!/usr/bin/env python3
"""
Candidate Extractor for Quantitative Fact-Grounding Enforcement in Manuscripts.
Scans docs/chapters/ to extract candidate paragraphs containing calculated statistics
or quantitative assertions (decimals, %, multipliers, units) and verifies the presence
of evidence anchors (Harvard citations, footnotes, docs/data/ references, or local tables).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

# Core morphological patterns for quantitative candidate extraction
CORE_NUMERIC_PATTERN = re.compile(
    r'\b\d+\.\d+\b|%|％|倍|ポイント',
    re.IGNORECASE
)

# False positive exclusion patterns (years, centuries, section numbers, page numbers)
YEAR_PATTERN = re.compile(r'\b(19|20)\d{2}年?\b')
CENTURY_PATTERN = re.compile(r'\b\d+世紀\b')
SECTION_NUM_PATTERN = re.compile(r'^\s*#*\s*\d+(\.\d+)*\b')
PAGE_NUM_PATTERN = re.compile(r'\bpp?\.\s*\d+\b', re.IGNORECASE)

# Evidence anchor patterns recognizing Harvard citations, footnotes, data links, and local table refs
EVIDENCE_ANCHOR_PATTERN = re.compile(
    r'\(\s*[A-Z][a-zA-Z\s&,.-]+,?\s*(19|20)\d{2}[a-z]?\s*\)|'  # Harvard citation (PSA, 2024)
    r'（\s*[^）]+,?\s*(19|20)\d{2}[a-z]?\s*）|'                 # Japanese citation （PSA, 2024）
    r'\[\^[\w-]+\]|'                                           # Markdown Footnote [^1]
    r'docs/(data|literature)/|'                                # Data link docs/data/...
    r'data:\s*docs/data/|'                                     # Data ID reference
    r'\(表\s*\d+-\d+\)|（表\s*\d+-\d+）|'                       # Table reference (表2-1)
    r'\([A-Z\s]+,\s*(19|20)\d{2}\)',                           # Institutional abbreviation (PSA, 2024)
    re.IGNORECASE
)


def load_custom_units(repo_root: Path) -> Set[str]:
    """Loads externalized unit terms from config/numeric_patterns.json if available."""
    config_file = repo_root / "config" / "numeric_patterns.json"
    units = set()
    if config_file.exists():
        try:
            data = json.loads(config_file.read_text(encoding="utf-8"))
            for key in ("units_ja", "units_en"):
                units.update(data.get(key, []))
        except Exception as e:
            print(f"⚠️ Warning: Failed to parse {config_file}: {e}", file=sys.stderr)
    return units


def clean_line_of_exclusions(line: str) -> str:
    """Removes false positives like years, section numbers, and page numbers before candidate checking."""
    line = SECTION_NUM_PATTERN.sub('', line)
    line = YEAR_PATTERN.sub('', line)
    line = CENTURY_PATTERN.sub('', line)
    line = PAGE_NUM_PATTERN.sub('', line)
    return line


def extract_paragraphs(text: str) -> List[Tuple[int, str]]:
    """Splits markdown text into paragraph blocks (separated by blank lines), returning (start_line_no, paragraph_text)."""
    lines = text.splitlines()
    paragraphs = []
    current_para = []
    para_start_line = 1
    in_code_block = False

    for idx, line in enumerate(lines, start=1):
        strip_line = line.strip()
        if strip_line.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block or strip_line.startswith("#") or strip_line.startswith("|") or strip_line.startswith("<!--") or strip_line.startswith("[^"):
            if current_para:
                paragraphs.append((para_start_line, "\n".join(current_para)))
                current_para = []
            continue

        if not strip_line:
            if current_para:
                paragraphs.append((para_start_line, "\n".join(current_para)))
                current_para = []
        else:
            if not current_para:
                para_start_line = idx
            current_para.append(line)

    if current_para:
        paragraphs.append((para_start_line, "\n".join(current_para)))

    return paragraphs


def find_ungrounded_claims(target_path: Path, repo_root: Path) -> List[Tuple[Path, int, str]]:
    """Scans manuscript markdown files for quantitative candidate paragraphs lacking evidence anchors."""
    violations = []
    custom_units = load_custom_units(repo_root)

    # Dynamic regex incorporating custom units
    custom_units_pattern = None
    if custom_units:
        escaped_units = [re.escape(u) for u in sorted(custom_units, key=len, reverse=True)]
        custom_units_pattern = re.compile(r'\b\d+\s*(' + '|'.join(escaped_units) + r')\b|\d+(' + '|'.join(escaped_units) + r')')

    if target_path.is_file():
        files = [target_path]
    elif target_path.is_dir():
        files = sorted(target_path.rglob("*.md"))
    else:
        return violations

    for md_file in files:
        if md_file.name == "references.md":
            continue
        text = md_file.read_text(encoding="utf-8")
        paragraphs = extract_paragraphs(text)

        for start_lineno, para_text in paragraphs:
            cleaned_para = clean_line_of_exclusions(para_text)

            is_candidate = bool(CORE_NUMERIC_PATTERN.search(cleaned_para))
            if not is_candidate and custom_units_pattern:
                is_candidate = bool(custom_units_pattern.search(cleaned_para))

            if is_candidate:
                # Check if evidence anchor exists anywhere in the paragraph
                if not EVIDENCE_ANCHOR_PATTERN.search(para_text):
                    snippet = para_text.replace("\n", " ").strip()[:80]
                    violations.append((md_file, start_lineno, snippet))

    return violations


def main():
    parser = argparse.ArgumentParser(description="Extract Quantitative Fact-Grounding Candidates in Manuscripts.")
    parser.add_argument("target", nargs="?", default="docs/chapters", help="Target manuscript directory or Markdown file to scan")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if ungrounded candidates are found")

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    target_path = Path(args.target).resolve()

    if not target_path.exists():
        print(f"Error: Target path '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Extracting Quantitative Candidate Paragraphs in {target_path}...")
    violations = find_ungrounded_claims(target_path, repo_root)

    if not violations:
        print("✅ All quantitative candidate paragraphs in manuscripts have valid evidence anchors!")
        sys.exit(0)
    else:
        print(f"⚠️ Found {len(violations)} quantitative candidate paragraph(s) requiring evidence verification:")
        for filepath, lineno, claim in violations[:15]:
            print(f"  ❌ {filepath.name}:{lineno} -> {claim}")
        if len(violations) > 15:
            print(f"  ... and {len(violations) - 15} more.")

        if args.strict:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
