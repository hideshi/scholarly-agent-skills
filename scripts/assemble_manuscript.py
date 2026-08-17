#!/usr/bin/env python3
"""
Assemble manuscript draft from chapters/, references.md, and appendix-*.md.

Usage:
  python3 assemble_manuscript.py <paper-id> [--repo-root PATH]

Output:
  docs/<paper-id>/manuscript/<paper-id>-draft.md
  (cognitive-scaffolding: cognitive-scaffolding-draft.md)
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

CHAPTER_FILES = [
    "chapter1-introduction.md",
    "chapter2-theoretical-framework.md",
    "chapter3-core-mechanisms.md",
    "chapter4-case-study.md",
    "chapter5-limitations-ethics.md",
    "chapter6-conclusion.md",
]

APPENDIX_FILES = [
    "appendix-a-glossary.md",
    "appendix-b-dialogue-excerpt.md",
    "appendix-c-audit-index.md",
]

DRAFT_NAMES = {
    "cognitive-scaffolding": "cognitive-scaffolding-draft.md",
}


def extract_abstract(outline_text: str) -> str:
    match = re.search(
        r"## 1\. アブストラクト[^\n]*\n+(.*?)\n---",
        outline_text,
        re.DOTALL,
    )
    if not match:
        raise ValueError("Abstract section not found in paper-outline.md")
    return match.group(1).strip()


def extract_titles(outline_text: str) -> tuple[str, str]:
    ja_match = re.search(r"\*\*論文仮題（和文）\*\*:\s*(.+)", outline_text)
    en_match = re.search(r"\*\*論文仮題（英文）\*\*:\s*(.+)", outline_text)
    if not ja_match or not en_match:
        raise ValueError("Title lines not found in paper-outline.md")
    ja_full = ja_match.group(1).strip()
    # Short title for H1: part before full-width colon subtitle
    ja_short = ja_full.split("：")[0].strip()
    return ja_short, en_match.group(1).strip()


def strip_chapter_references(text: str) -> str:
    """Remove per-chapter ## 参考文献 section (and preceding ---)."""
    match = re.search(r"\n---\s*\n\n## 参考文献[^\n]*\n", text)
    if match:
        return text[: match.start()].rstrip() + "\n"
    return text.rstrip() + "\n"


def assemble(paper_id: str, repo_root: Path) -> str:
    base = repo_root / "docs" / paper_id
    outline_path = base / "design" / "sot" / "paper-outline.md"
    if not outline_path.is_file():
        outline_path = base / "design" / "paper-outline.md"
    outline = outline_path.read_text(encoding="utf-8")
    ja_title, en_title = extract_titles(outline)
    abstract = extract_abstract(outline)

    parts: list[str] = [
        f"# {ja_title}",
        "",
        f"> **{en_title}**",
        "",
        f"<!-- AUTO-ASSEMBLED from chapters/ + references.md + manuscript/appendix-*.md. Regenerated {date.today().isoformat()}. -->",
        "",
        "---",
        "",
        "## アブストラクト",
        "",
        abstract,
        "",
        "---",
        "",
    ]

    chapters_dir = base / "chapters"
    for name in CHAPTER_FILES:
        path = chapters_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing chapter: {path}")
        body = strip_chapter_references(path.read_text(encoding="utf-8"))
        parts.append(body)
        if not body.endswith("\n"):
            parts.append("")

    # Chapter 6 inheritance note (replaces stripped per-chapter refs footer)
    parts.extend(["---", "", "", "Yin (2018) ほか各章引用文献を継承する。", "", "---", ""])

    refs_path = chapters_dir / "references.md"
    if not refs_path.is_file():
        raise FileNotFoundError(f"Missing references: {refs_path}")
    parts.append(refs_path.read_text(encoding="utf-8").rstrip())
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("# 付録")
    parts.append("")

    manuscript_dir = base / "manuscript"
    for name in APPENDIX_FILES:
        path = manuscript_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing appendix: {path}")
        parts.append(path.read_text(encoding="utf-8").rstrip())
        parts.append("")
        parts.append("---")
        parts.append("")

    return "\n".join(parts).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper_id", help="Paper ID under docs/<paper-id>/")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Override output path",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    content = assemble(args.paper_id, repo_root)

    if args.output:
        out_path = args.output.resolve()
    else:
        draft_name = DRAFT_NAMES.get(args.paper_id, f"{args.paper_id}-draft.md")
        out_path = repo_root / "docs" / args.paper_id / "manuscript" / draft_name

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(f"Assembled: {out_path} ({len(content.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
