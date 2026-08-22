#!/usr/bin/env python3
"""
Assemble manuscript draft from chapters/, references.md, and appendix-*.md.

Usage:
  python3 assemble_manuscript.py <paper-id> [--repo-root PATH]

Output (default):
  docs/<paper-id>/manuscript/<論文正式タイトル（和文仮題）>.md

Naming follows rules/ja/academic-writing.md Official Paper Title Filename Rule
and AGENTS.md `[paper_title].md` convention. paper-id is used only as the
docs/ directory key, not as the deliverable basename.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

# Fallback only when chapters/ has no chapter*.md (should not happen).
# Discovery is by filename: chapter*.md sorted by leading number.
APPENDIX_GLOB = "appendix-*.md"

# Characters illegal or awkward in cross-platform filenames
_UNSAFE_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def extract_abstract(outline_text: str) -> str:
    match = re.search(
        r"## 1\. アブストラクト[^\n]*\n+(.*?)\n---",
        outline_text,
        re.DOTALL,
    )
    if not match:
        raise ValueError("Abstract section not found in paper-outline.md")
    return match.group(1).strip()


def extract_titles(outline_text: str) -> tuple[str, str, str]:
    """Return (ja_short_for_h1, ja_full_for_filename, en_title)."""
    ja_match = re.search(r"\*\*論文仮題（和文）\*\*:\s*(.+)", outline_text)
    en_match = re.search(r"\*\*論文仮題（英文）\*\*:\s*(.+)", outline_text)
    if not ja_match or not en_match:
        raise ValueError("Title lines not found in paper-outline.md")
    ja_full = ja_match.group(1).strip()
    # Short title for H1: part before full-width colon subtitle
    ja_short = ja_full.split("：")[0].strip()
    return ja_short, ja_full, en_match.group(1).strip()


_BIBLIO_FIELDS = (
    ("著者", "著者"),
    ("所属", "所属"),
    ("日付", "日付"),
    ("ライセンス", "ライセンス"),
    ("バージョン", "バージョン"),
    ("DOI", "DOI"),
)


def extract_biblio_lines(outline_text: str) -> list[str]:
    """Return markdown list lines for author/affiliation if present."""
    lines: list[str] = []
    for key, label in _BIBLIO_FIELDS:
        match = re.search(rf"\*\*{re.escape(key)}\*\*:\s*(.+)", outline_text)
        if match:
            lines.append(f"- **{label}**: {match.group(1).strip()}")
    return lines


def title_to_filename(title: str, suffix: str = ".md") -> str:
    """Map official paper title to a filesystem-safe deliverable basename."""
    name = title.strip()
    # Prefer full-width analogues for path separators / colon
    name = (
        name.replace("\\", "＼")
        .replace("/", "／")
        .replace(":", "：")
        .replace("*", "＊")
        .replace("?", "？")
        .replace('"', "＂")
        .replace("<", "＜")
        .replace(">", "＞")
        .replace("|", "｜")
    )
    name = _UNSAFE_FILENAME_CHARS.sub("", name)
    name = name.strip(" .")
    if not name:
        raise ValueError("Empty title after filename sanitization")
    if not suffix.startswith("."):
        suffix = f".{suffix}"
    return f"{name}{suffix}"


def strip_chapter_references(text: str) -> str:
    """Remove per-chapter ## 参考文献 section (and preceding ---)."""
    match = re.search(r"\n---\s*\n\n## 参考文献[^\n]*\n", text)
    if match:
        return text[: match.start()].rstrip() + "\n"
    return text.rstrip() + "\n"


def discover_chapter_files(chapters_dir: Path) -> list[Path]:
    """Return chapter*.md paths sorted by the leading chapter number."""
    files = [p for p in chapters_dir.glob("chapter*.md") if p.is_file()]
    if not files:
        raise FileNotFoundError(f"No chapter*.md files in {chapters_dir}")

    def sort_key(path: Path) -> tuple[int, str]:
        match = re.match(r"chapter(\d+)", path.name)
        number = int(match.group(1)) if match else 10**6
        return (number, path.name)

    return sorted(files, key=sort_key)


def discover_appendix_files(manuscript_dir: Path) -> list[Path]:
    """Return appendix-*.md paths if present. Empty list is allowed."""
    if not manuscript_dir.is_dir():
        return []
    return sorted(p for p in manuscript_dir.glob(APPENDIX_GLOB) if p.is_file())


def assemble(paper_id: str, repo_root: Path) -> tuple[str, str]:
    """Assemble manuscript text and return (content, ja_full_title)."""
    base = repo_root / "docs" / paper_id
    outline_path = base / "design" / "sot" / "paper-outline.md"
    if not outline_path.is_file():
        outline_path = base / "design" / "paper-outline.md"
    outline = outline_path.read_text(encoding="utf-8")
    ja_title, ja_full, en_title = extract_titles(outline)
    abstract = extract_abstract(outline)
    biblio = extract_biblio_lines(outline)

    parts: list[str] = [
        f"# {ja_title}",
        "",
        f"> **{en_title}**",
        "",
    ]
    if biblio:
        parts.extend(biblio)
        parts.append("")
    parts.extend(
        [
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
    )

    chapters_dir = base / "chapters"
    for path in discover_chapter_files(chapters_dir):
        body = strip_chapter_references(path.read_text(encoding="utf-8"))
        parts.append(body)
        if not body.endswith("\n"):
            parts.append("")

    refs_path = chapters_dir / "references.md"
    if not refs_path.is_file():
        raise FileNotFoundError(f"Missing references: {refs_path}")
    parts.extend(["---", ""])
    parts.append(refs_path.read_text(encoding="utf-8").rstrip())
    parts.append("")

    manuscript_dir = base / "manuscript"
    appendices = discover_appendix_files(manuscript_dir)
    if appendices:
        parts.extend(["---", "", "# 付録", ""])
        for path in appendices:
            parts.append(path.read_text(encoding="utf-8").rstrip())
            parts.append("")
            parts.append("---")
            parts.append("")

    return "\n".join(parts).rstrip() + "\n", ja_full


def run_gate_script(script_name: str, chapters: Path) -> int:
    """Run a gate script on chapters/. Returns its exit code (0 if missing)."""
    script = SCRIPTS_DIR / script_name
    if not script.is_file():
        print(f"⚠️ gate script not found: {script} (skipped)", file=sys.stderr)
        return 0
    res = subprocess.run(
        [sys.executable, str(script), str(chapters)],
        capture_output=True,
        text=True,
    )
    out = ((res.stdout or "") + (("\n" + res.stderr) if res.stderr else "")).strip()
    print(out)
    return res.returncode


def run_prose_gates(paper_id: str, repo_root: Path) -> int:
    """Fail-stop gates on manuscript prose. Returns non-zero if any FAILs."""
    chapters = repo_root / "docs" / paper_id / "chapters"
    rc = run_gate_script("check_reviewer_readability.py", chapters)
    rc |= run_gate_script("check_terminology_consistency.py", chapters)
    rc |= run_gate_script("check_sensitive_expression.py", chapters)
    return rc


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
    parser.add_argument(
        "--force",
        action="store_true",
        help="Assemble even if the prose gates (readability/terminology) report FAIL",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    content, ja_full = assemble(args.paper_id, repo_root)

    gate_rc = run_prose_gates(args.paper_id, repo_root)
    if gate_rc != 0 and not args.force:
        print(
            "💥 Assembly aborted: prose gate reported FAIL. "
            "Fix findings or re-run with --force.",
            file=sys.stderr,
        )
        return 1

    if args.output:
        out_path = args.output.resolve()
    else:
        draft_name = title_to_filename(ja_full, ".md")
        out_path = repo_root / "docs" / args.paper_id / "manuscript" / draft_name

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(f"Assembled: {out_path} ({len(content.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
