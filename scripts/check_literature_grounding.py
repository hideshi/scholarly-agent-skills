#!/usr/bin/env python3
"""
Verify that in-text academic citations in manuscript chapters have grounded
artifacts under docs/literature/papers/*.md, and that status=full-text notes
have a matching primary-source PDF under papers/_downloads/{slug}.pdf.

Join keys (priority): DOI > arXiv ID > author surname + year (frontmatter).
Exit codes: 0 = PASS/WARN only, 1 = at least one FAIL.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from check_citation_format import (
    extract_citations_from_text,
    extract_primary_surname,
    is_author_matched,
    parse_literature_matrix,
)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
MIN_FULL_TEXT_CHARS = 500
SKIP_PAPER_NAMES = {"_ingestion-log", "_manual-ingestion-required"}


@dataclass
class PaperRecord:
    path: Path
    title: str
    authors: str
    year: str
    doi: str
    arxiv_id: str
    status: str
    body_chars: int
    source_pdf: Optional[Path] = None


@dataclass
class GroundingResult:
    author: str
    year: str
    lineno: int
    source_file: Path
    verdict: str  # PASS | WARN | FAIL
    paper_path: Optional[Path]
    reason: str


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    meta: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"').strip("'")
    body = text[match.end() :]
    return meta, body


def normalize_doi(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    return value


def normalize_arxiv(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^https?://arxiv\.org/abs/", "", value)
    value = value.replace("arxiv:", "")
    return value


def resolve_source_pdf(papers_dir: Path, stem: str) -> Optional[Path]:
    """Return the primary-source PDF next to the note, if present."""
    for name in (f"{stem}.pdf", f"{stem}.PDF"):
        candidate = papers_dir / "_downloads" / name
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    return None


def load_paper_records(papers_dir: Path) -> List[PaperRecord]:
    records: List[PaperRecord] = []
    if not papers_dir.exists():
        return records

    for path in sorted(papers_dir.glob("*.md")):
        if path.stem.startswith("_") or path.stem in SKIP_PAPER_NAMES:
            continue
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        records.append(
            PaperRecord(
                path=path,
                title=meta.get("title", ""),
                authors=meta.get("authors", meta.get("author", "")),
                year=meta.get("year", ""),
                doi=normalize_doi(meta.get("doi", "")),
                arxiv_id=normalize_arxiv(meta.get("arxiv_id", "")),
                status=meta.get("status", "unknown"),
                body_chars=len(body.strip()),
                source_pdf=resolve_source_pdf(papers_dir, path.stem),
            )
        )
    return records


def find_matching_paper(
    author: str,
    year: str,
    papers: List[PaperRecord],
    matrix_entries: List[Dict[str, str]],
) -> Optional[PaperRecord]:
    cited_surname = extract_primary_surname(author)

    matrix_doi = ""
    matrix_arxiv = ""
    for entry in matrix_entries:
        if is_author_matched(author, year, [entry]):
            url = entry.get("doi_or_url", "")
            if "arxiv.org" in url.lower():
                matrix_arxiv = normalize_arxiv(url)
            elif "doi.org" in url.lower() or url.startswith("10."):
                matrix_doi = normalize_doi(url)

    for paper in papers:
        if paper.year and paper.year != year:
            continue
        paper_surname = extract_primary_surname(paper.authors)
        author_match = (
            cited_surname
            and (
                cited_surname in paper.authors.lower()
                or cited_surname == paper_surname
            )
        )
        if matrix_doi and paper.doi and matrix_doi == paper.doi:
            return paper
        if matrix_arxiv and paper.arxiv_id and matrix_arxiv == paper.arxiv_id:
            return paper
        if author_match:
            return paper
    return None


def classify_paper(paper: Optional[PaperRecord]) -> Tuple[str, str]:
    if paper is None:
        return "FAIL", "no matching literature/papers/*.md artifact"

    status = paper.status.lower()
    if status == "full-text":
        if paper.body_chars < MIN_FULL_TEXT_CHARS:
            return (
                "WARN",
                f"status=full-text but body has only {paper.body_chars} chars "
                f"(min {MIN_FULL_TEXT_CHARS}); possible abstract-only or scan PDF",
            )
        if paper.source_pdf is None:
            return (
                "WARN",
                f"status=full-text but no PDF at _downloads/{paper.path.stem}.pdf; "
                "markdown note is a transcription, not the primary source",
            )
        return "PASS", f"grounded at {paper.path.name} (PDF: {paper.source_pdf.name})"

    if status in {"manual-stub", "abstract-only"}:
        return "WARN", f"status={status} at {paper.path.name}"

    return "WARN", f"unknown status={paper.status} at {paper.path.name}"


NARRATIVE_CITATION_PATTERN = re.compile(
    r"(?<![\[\(])"
    r"([A-Z][A-Za-z\-]+(?:\s+[A-Z][a-z]+)?"
    r"(?:\s+et\s+al\.?)?"
    r"(?:\s+and\s+[A-Z][a-z]+(?:\s+[A-Z]\.)?)?)"
    r"\s+\((\d{4}[a-z]?)\)"
)
COMMA_LIST_CITATION_PATTERN = re.compile(
    r"([A-Z][A-Za-z]+(?:,\s+[A-Z][A-Za-z]+)*(?:,\s+and\s+[A-Z][a-z]+)?)\s+\((\d{4}[a-z]?)\)"
)


def dedupe_subsumed_citations(citations: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Drop shorter author keys subsumed by a longer key on the same line/year."""
    unique = list(dict.fromkeys(citations))
    unique.sort(key=lambda x: len(x[0]), reverse=True)
    kept: List[Tuple[str, str]] = []
    for author, year in unique:
        if any(author != other and author in other and year == y for other, y in kept):
            continue
        kept.append((author, year))
    return kept


def extract_narrative_citations_from_line(line: str) -> List[Tuple[str, str]]:
    """Extract (author, year) from narrative citations like `Barkley (2012)`."""
    citations: List[Tuple[str, str]] = []
    comma_spans: List[Tuple[int, int]] = []

    for match in COMMA_LIST_CITATION_PATTERN.finditer(line):
        author = match.group(1).strip()
        year = match.group(2).strip()
        citations.append((author, year))
        comma_spans.append((match.start(), match.end()))

    for match in NARRATIVE_CITATION_PATTERN.finditer(line):
        if any(start <= match.start() < end for start, end in comma_spans):
            continue
        author = match.group(1).strip()
        year = match.group(2).strip()
        if len(author) > 1 and not author.isdigit():
            citations.append((author, year))
    return dedupe_subsumed_citations(citations)


def extract_all_citations_from_file(filepath: Path) -> List[Tuple[int, str, str]]:
    text = filepath.read_text(encoding="utf-8")
    found: List[Tuple[int, str, str]] = []
    seen: Set[Tuple[str, str]] = set()

    for lineno, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("## 参考文献") or line.strip().startswith("## References"):
            break
        if line.strip().startswith("#") or line.strip().startswith("|") or line.strip().startswith("- "):
            continue
        for author, year in extract_citations_from_text(line):
            key = (author.lower(), year)
            if key not in seen:
                seen.add(key)
                found.append((lineno, author, year))
        for author, year in extract_narrative_citations_from_line(line):
            key = (author.lower(), year)
            if key not in seen:
                seen.add(key)
                found.append((lineno, author, year))

    return found


def collect_citations(paths: List[Path]) -> List[Tuple[Path, int, str, str]]:
    found: List[Tuple[Path, int, str, str]] = []

    for path in paths:
        for lineno, author, year in extract_all_citations_from_file(path):
            found.append((path, lineno, author, year))
    return found


def audit_grounding(
    chapter_paths: List[Path],
    papers_dir: Path,
    matrix_path: Optional[Path],
) -> List[GroundingResult]:
    matrix_entries = parse_literature_matrix(matrix_path) if matrix_path else []
    papers = load_paper_records(papers_dir)
    citations = collect_citations(chapter_paths)

    results: List[GroundingResult] = []
    for source_file, lineno, author, year in citations:
        paper = find_matching_paper(author, year, papers, matrix_entries)
        verdict, reason = classify_paper(paper)
        results.append(
            GroundingResult(
                author=author,
                year=year,
                lineno=lineno,
                source_file=source_file,
                verdict=verdict,
                paper_path=paper.path if paper else None,
                reason=reason,
            )
        )
    return results


def print_report(results: List[GroundingResult]) -> None:
    if not results:
        print("ℹ️  No in-text citations found.")
        return

    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for result in results:
        counts[result.verdict] += 1

    print(f"📚 Literature grounding: {len(results)} unique citation(s)")
    for result in results:
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[result.verdict]
        loc = f"{result.source_file}:{result.lineno}"
        print(
            f"  {icon} ({result.author}, {result.year}) @ {loc} "
            f"→ {result.verdict}: {result.reason}"
        )

    print(
        f"\nSummary: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}"
    )


def resolve_paths(raw_paths: List[Path]) -> List[Path]:
    files: List[Path] = []
    for p in raw_paths:
        if p.is_file() and p.suffix == ".md":
            files.append(p)
        elif p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
    return files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check that chapter citations are grounded in literature/papers/*.md"
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Chapter markdown file(s) or directory",
    )
    parser.add_argument(
        "--papers-dir",
        type=Path,
        default=Path("docs/literature/papers"),
        help="Directory containing grounded paper markdown files",
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        default=None,
        help="Optional literature-matrix.md for DOI/arXiv join keys",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on WARN as well as FAIL",
    )
    args = parser.parse_args()

    chapter_paths = resolve_paths(args.paths)
    if not chapter_paths:
        print("No markdown files found.", file=sys.stderr)
        sys.exit(1)

    matrix_path = args.matrix
    if matrix_path is None:
        candidate = Path("docs/literature/literature-matrix.md")
        if candidate.exists():
            matrix_path = candidate

    results = audit_grounding(chapter_paths, args.papers_dir, matrix_path)
    print_report(results)

    if any(r.verdict == "FAIL" for r in results):
        sys.exit(1)
    if args.strict and any(r.verdict == "WARN" for r in results):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
