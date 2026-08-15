#!/usr/bin/env python3
"""
Check citation traceability and footnote consistency in Markdown paper drafts.
Scans for citations in both Harvard/APA style (Author Year / 組織名 / 和文著者) and Footnote style [^1],
verifying that every citation has a matching entry in literature-matrix.md and auto-generating references.md.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Institutional name & acronym mapping for alphabetical sorting
INSTITUTION_FULL_NAMES = {
    "PSA": "Philippine Statistics Authority (PSA)",
    "World Bank": "World Bank",
    "ADB": "Asian Development Bank (ADB)",
    "DSWD": "Department of Social Welfare and Development (DSWD)",
    "PIDS": "Philippine Institute for Development Studies (PIDS)",
    "UNDP": "United Nations Development Programme (UNDP)",
    "BSP": "Bangko Sentral ng Pilipinas (BSP)",
    "DBM": "Department of Budget and Management (DBM)",
    "NEA": "National Electrification Administration (NEA)",
    "BARMM": "Bangsamoro Autonomous Region in Muslim Mindanao (BARMM)",
    "BOL": "Bangsamoro Organic Law (BOL)",
    "RA 11310": "Republic Act No. 11310",
}

PARENTHESIS_PATTERN = re.compile(r'[（\(]([^（\)]+?)[）\)]')
SINGLE_CITATION_PATTERN = re.compile(r'^\s*([一-龯ぁ-んァ-ヶA-Za-z0-9\s&,\.・\-\+]+?)[,\s]+(\d{4}[a-z]?)\s*$')


def parse_literature_matrix(matrix_path: Path) -> List[Dict[str, str]]:
    """Parses docs/literature/literature-matrix.md to extract metadata for all registered papers."""
    entries = []
    if not matrix_path.exists():
        return entries

    content = matrix_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    for line in lines:
        sline = line.strip()
        if not sline.startswith("|") or "文献名" in sline or "著者" in sline or "---" in sline or "DOI" in sline:
            continue

        parts = [p.strip() for p in sline.split("|")[1:-1]]
        if len(parts) >= 7:
            link_or_doi, title, author, year, method, findings, theme = parts[:7]
            star_rating = parts[7] if len(parts) >= 8 else ""

            doi_match = re.search(r'\[(.*?)\]\((.*?)\)', link_or_doi)
            url = doi_match.group(2) if doi_match else link_or_doi

            entries.append({
                "doi_or_url": url,
                "title": title,
                "author": author,
                "year": year,
                "method": method,
                "findings": findings,
                "theme": theme,
                "rating": star_rating
            })

    return entries


def extract_citations_from_text(text: str) -> List[Tuple[str, str]]:
    """Extracts (author_part, year_part) tuples from text line by line."""
    citations = []
    lines = text.splitlines()

    for line in lines:
        sline = line.strip()
        if sline.startswith("#") or sline.startswith("<!--") or sline.startswith("|") or sline.startswith("[^"):
            continue

        for p_match in PARENTHESIS_PATTERN.finditer(sline):
            inside = p_match.group(1).strip()
            items = [item.strip() for item in re.split(r'[;；]', inside)]

            for item in items:
                c_match = SINGLE_CITATION_PATTERN.match(item)
                if c_match:
                    author_part = c_match.group(1).strip()
                    year_part = c_match.group(2).strip()

                    if not author_part.isdigit() and len(author_part) > 1:
                        citations.append((author_part, year_part))

    return citations


def extract_primary_surname(author_str: str) -> str:
    """Extracts primary surname or acronym token for matching (e.g. 'Barrios et al.' -> 'barrios', 'World Bank' -> 'world bank')."""
    clean = re.sub(r'\s+et\s+al\.?', '', author_str, flags=re.IGNORECASE).strip().lower()
    if "," in clean and not any(kw in clean for kw in ("bank", "authority", "department", "programme")):
        clean = clean.split(",")[0].strip()
    words = clean.split()
    return words[0] if words else clean


def is_author_matched(cited_author: str, cited_year: str, matrix_entries: List[Dict[str, str]]) -> bool:
    """Checks if cited_author and cited_year match any entry in literature_matrix."""
    cited_lower = cited_author.lower()
    cited_surname = extract_primary_surname(cited_author)

    for entry in matrix_entries:
        m_year = entry["year"]
        if m_year != cited_year:
            continue

        m_author_lower = entry["author"].lower()
        m_surname = extract_primary_surname(entry["author"])

        if cited_lower in m_author_lower or m_author_lower in cited_lower:
            return True

        if cited_surname and (cited_surname in m_author_lower or cited_surname == m_surname):
            return True

        if cited_author.upper() in entry["author"].upper():
            return True

    return False


def check_citations_in_file(filepath: Path) -> Tuple[List[str], List[str], List[Tuple[int, str, str]]]:
    """Scans a markdown file for footnote definitions and Harvard citations."""
    errors = []
    warnings = []
    citations_found = []

    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    footnote_refs: Set[str] = set()
    footnote_defs: Set[str] = set()

    fn_ref_pattern = re.compile(r'\[\^([\w-]+)\](?!\s*:)')
    fn_def_pattern = re.compile(r'^\[\^([\w-]+)\]\s*:')

    in_code_block = False
    for lineno, line in enumerate(lines, 1):
        sline = line.strip()
        if sline.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        m_def = fn_def_pattern.match(sline)
        if m_def:
            footnote_defs.add(m_def.group(1))

        for m_ref in fn_ref_pattern.finditer(sline):
            footnote_refs.add(m_ref.group(1))

        for author_part, year_part in extract_citations_from_text(line):
            citations_found.append((lineno, author_part, year_part))

    missing_defs = footnote_refs - footnote_defs
    for m in sorted(missing_defs):
        errors.append(f"ERROR: Footnote reference '[^{m}]' has no matching definition '[^{m}]:'")

    unused_defs = footnote_defs - footnote_refs
    for u in sorted(unused_defs):
        warnings.append(f"WARNING: Footnote definition '[^{u}]:' exists but is never referenced in text")

    return errors, warnings, citations_found


def generate_references_markdown(entries: List[Dict[str, str]]) -> str:
    """Generates clean APA/Harvard formatted references.md from literature-matrix.md entries."""
    header = (
        "<!-- AUTO-GENERATED from docs/literature/literature-matrix.md. Do not edit manually. -->\n"
        "# 参考文献 (References)\n\n"
    )

    formatted_entries = []

    for entry in entries:
        author = entry["author"]
        year = entry["year"]
        title = entry["title"]
        url = entry["doi_or_url"]

        sort_key = INSTITUTION_FULL_NAMES.get(author, author)

        if url.startswith("http"):
            citation_line = f"- **{author}** ({year}). *{title}*. Available at: [{url}]({url})."
        else:
            citation_line = f"- **{author}** ({year}). *{title}*. {url}."

        formatted_entries.append((sort_key, citation_line))

    formatted_entries.sort(key=lambda x: x[0].lower())

    lines = [header]
    for _, line in formatted_entries:
        lines.append(line + "\n")

    return "\n".join(lines).strip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Check citation traceability and auto-generate references.md.")
    parser.add_argument("paths", nargs="*", type=Path, help="Markdown file(s) or directory to check")
    parser.add_argument("--matrix", type=Path, help="Path to docs/literature/literature-matrix.md for SoT cross-referencing")
    parser.add_argument("--generate-references", type=Path, help="Output path for auto-generated references.md")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if errors or warnings are found")

    args = parser.parse_args()

    if args.generate_references:
        matrix_path = args.matrix or Path("docs/literature/literature-matrix.md")
        if not matrix_path.exists():
            print(f"Error: Matrix path '{matrix_path}' does not exist.", file=sys.stderr)
            sys.exit(1)

        entries = parse_literature_matrix(matrix_path)
        ref_text = generate_references_markdown(entries)
        args.generate_references.parent.mkdir(parents=True, exist_ok=True)
        args.generate_references.write_text(ref_text, encoding="utf-8")
        print(f"✅ Auto-generated references.md ({len(entries)} entries) -> {args.generate_references}")
        if not args.paths:
            sys.exit(0)

    target_files: List[Path] = []
    for p in args.paths:
        if p.is_file() and p.suffix == ".md":
            target_files.append(p)
        elif p.is_dir():
            target_files.extend(sorted(p.rglob("*.md")))

    if not target_files:
        print("No Markdown files found to check.", file=sys.stderr)
        sys.exit(1)

    print(f"📖 Checking {len(target_files)} Markdown file(s)...")

    matrix_entries = []
    if args.matrix and args.matrix.exists():
        matrix_entries = parse_literature_matrix(args.matrix)

    total_errors = 0
    total_warnings = 0

    for filepath in target_files:
        errors, warnings, citations_found = check_citations_in_file(filepath)

        for lineno, author, year in citations_found:
            if matrix_entries:
                if not is_author_matched(author, year, matrix_entries):
                    warnings.append(f"WARNING: Citation ({author}, {year}) at L{lineno} is not registered in literature-matrix.md!")

        total_errors += len(errors)
        total_warnings += len(warnings)

        if errors or warnings:
            print(f"\n📄 {filepath}:")
            for err in errors:
                print(f"  ❌ {err}")
            for warn in warnings:
                print(f"  ⚠️ {warn}")

    if total_errors == 0 and total_warnings == 0:
        print("✅ All citations, footnotes, and literature matrix entries are properly paired.")

    if args.strict and (total_errors > 0 or total_warnings > 0):
        sys.exit(1)
    elif total_errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
