#!/usr/bin/env python3
"""
Reviewer-Readability Check for academic paper manuscripts.

Detects internal workflow symbols (coding-scheme IDs, protocol versions,
wall-clock timestamps, internal jargon) leaking into manuscript prose that
external reviewers cannot interpret. Also checks section-number integrity
(branch-suffixed insertion traces like 3.2b, gaps, duplicates, and dangling
§x.y cross-references) for the review phase.

Three-layer vocabulary policy (rules/ja/reviewer-readability-rule.md):
  1. Prose   — academic description only; internal codes removed
  2. Tables  — codes allowed with Japanese gloss (lines starting with '|')
  3. Blockquotes / code fences / appendices — reference layer, exempt

Allowed gloss forms in prose (not violations):
  - Parenthesized ID:      「...が観察された（NC-05）」「用語確認の質問（RQ-TERM）」
  - ID followed by gloss:  「NC-01（図表の却下）」

Inline suppression: a line containing '<!-- readability:ignore -->' is skipped
(deliberate exceptions; must be approved by the author and recorded in triage).

Exit codes: 0 = PASS / WARN, 1 = at least one FAIL.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

IGNORE_MARKER = "<!-- readability:ignore -->"

# Internal coding-scheme IDs that must not drive prose sentences.
CODE_PATTERN = re.compile(
    r"\b(?:PROP-(?:ADOPT|REJECT|INIT)|SCAF-FAIL|REC-ERR|DEP-RISK|"
    r"RQ-(?:TERM|VALID|SCOPE|MAP)|PH-(?:REV|CON|DRF))\b"
)
NC_PATTERN = re.compile(r"\bNC-\d+\b")
JST_PATTERN = re.compile(r"\b\d{1,2}:\d{2}\s*JST\b")
VERSION_PATTERN = re.compile(r"\bv\d+\.\d+\.\d+\b")
JARGON_PATTERN = re.compile(r"\b(?:grounding|ingestion|stub)\b", re.IGNORECASE)

# Section-number integrity (校閲期の編集痕検出):
#   branch   — letter-suffixed numbers (3.2b) are insertion traces from drafting
#   gap      — missing numbers in a heading sequence (3.1 -> 3.3)
#   dup      — the same heading number twice in one file
#   dangling — a §x.y reference whose target heading does not exist
SECNUM_HEADING = re.compile(r"^(#{1,6})\s*(\d+(?:\.\d+)+)([a-z])?\b")
SECNUM_BRANCH = re.compile(r"\b\d+\.\d+[a-z]\b")
SECNUM_REF = re.compile(r"§\s*(\d+\.\d+)(?!\.)")

# Parenthetical spans (full/half width) and "ID（gloss）" adjacency are glosses.
_PAREN_SPAN = re.compile(r"（[^（）]*）|\([^()]*\)")

# Internal design docs are the system of record for codes; never flag them.
EXCLUDED_FILENAMES = ("test-cases.md", "evidence-gate-report.md", "references.md")

HINTS = {
    "code": "内部コードが本文で使用されています。日本語説明＋括弧内ID（prose-gloss）に改めるか、本文から除去してください",
    "nc": "負例IDが括弧外で使用されています。「〇〇という事例（NC-xx）」の形に改めてください",
    "jst": "時刻が本文に出ています。監査索引用の表への集約を検討してください（主題言及なら要著者承認）",
    "version": "バージョン番号が本文に出ています。プロトコル仕様そのものが主題か確認してください",
    "jargon": "内部工程語の可能性があります。日本語化または括弧内 gloss を検討してください",
    "density": "1行に内部コードが密集しています。段落の分割・日本語化を検討してください",
    "secnum-branch": "枝番（3.2b 等）は執筆過程の編集痕です。最終版では連番にリナンバリングし、本文中の参照も一括更新してください",
    "secnum-gap": "節番号に欠番があります。意図的な欠番か確認してください",
    "secnum-dup": "節番号が重複しています。見出しを連番に修正してください",
    "secnum-dangling": "§ 参照先の節が見つかりません。外部文献の節参照なら対応不要です",
}


@dataclass
class Finding:
    path: Path
    line: int
    severity: str  # "FAIL" | "WARN"
    kind: str
    match: str
    snippet: str


def strip_glosses(line: str) -> str:
    """Remove 'ID（gloss）' adjacency and parenthetical spans from a line."""
    stripped = re.sub(r"\bNC-\d+(?=（)", " ", line)
    stripped = re.sub(
        r"\b(?:PROP-(?:ADOPT|REJECT|INIT)|SCAF-FAIL|REC-ERR|DEP-RISK|"
        r"RQ-(?:TERM|VALID|SCOPE|MAP)|PH-(?:REV|CON|DRF))(?=（)",
        " ",
        stripped,
    )
    return _PAREN_SPAN.sub(" ", stripped)


def iter_prose_lines(content: str) -> List[Tuple[int, str]]:
    """Yield (line_number, line) excluding tables, blockquotes, code fences."""
    in_fence = False
    for idx, raw in enumerate(content.splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped or stripped.startswith("|") or stripped.startswith(">"):
            continue
        if IGNORE_MARKER in raw:
            continue
        yield idx, raw


def collect_sections(files: List[Path]) -> set:
    """Build the set of section numbers defined by headings across files."""
    sections = set()
    for fp in files:
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception:
            continue
        for raw in content.splitlines():
            m = SECNUM_HEADING.match(raw.strip())
            if m:
                sections.add(m.group(2) + (m.group(3) or ""))
                sections.add(m.group(2))
    return sections


def scan_file(file_path: Path, known_sections: set | None = None) -> List[Finding]:
    findings: List[Finding] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}", file=sys.stderr)
        return findings

    if known_sections is None:
        known_sections = collect_sections([file_path])

    headings: List[Tuple[int, str, str]] = []  # (line_no, base, suffix)

    for line_no, line in iter_prose_lines(content):
        body = strip_glosses(line)
        snippet = line.strip()[:80]

        codes = CODE_PATTERN.findall(body)
        for code in codes:
            findings.append(Finding(file_path, line_no, "FAIL", "code", code, snippet))
        if len(codes) >= 3:
            findings.append(Finding(file_path, line_no, "WARN", "density", f"{len(codes)} codes", snippet))

        for m in NC_PATTERN.findall(body):
            findings.append(Finding(file_path, line_no, "FAIL", "nc", m, snippet))

        for m in JST_PATTERN.findall(body):
            findings.append(Finding(file_path, line_no, "WARN", "jst", m, snippet))
        for m in VERSION_PATTERN.findall(body):
            findings.append(Finding(file_path, line_no, "WARN", "version", m, snippet))

        jargon_line = _PAREN_SPAN.sub(" ", line)
        for m in JARGON_PATTERN.findall(jargon_line):
            findings.append(Finding(file_path, line_no, "WARN", "jargon", m, snippet))

        heading = SECNUM_HEADING.match(line.strip())
        if heading:
            headings.append((line_no, heading.group(2), heading.group(3) or ""))

        for m in set(SECNUM_BRANCH.findall(body)):
            findings.append(Finding(file_path, line_no, "FAIL", "secnum-branch", m, snippet))

        for ref in set(SECNUM_REF.findall(body)):
            if ref not in known_sections:
                findings.append(Finding(file_path, line_no, "WARN", "secnum-dangling", f"§{ref}", snippet))

    # Heading sequence: duplicates (exact token) and gaps in the numeric tail.
    seen: dict[str, int] = {}
    for line_no, base, suffix in headings:
        token = base + suffix
        if token in seen:
            findings.append(Finding(file_path, line_no, "FAIL", "secnum-dup", token, f"line {seen[token]} との重複"))
        else:
            seen[token] = line_no
    twos = [
        (tuple(int(p) for p in base.split(".")[:2]), line_no)
        for line_no, base, _ in headings
        if base.count(".") == 1
    ]
    deduped = sorted({num for num, _ in twos})
    first_line = {num: line for num, line in reversed(twos)}
    for (x1, y1), (x2, y2) in zip(deduped, deduped[1:]):
        if x1 == x2 and y2 - y1 > 1:
            missing = ", ".join(f"{x1}.{y}" for y in range(y1 + 1, y2))
            findings.append(
                Finding(file_path, first_line[(x2, y2)], "WARN", "secnum-gap", missing, f"{x1}.{y1} と {x2}.{y2} の間に欠番")
            )

    return findings


def scan_target(target_path: Path) -> List[Finding]:
    all_findings: List[Finding] = []
    if target_path.is_file():
        files = [target_path]
    elif target_path.is_dir():
        files = [
            f for f in target_path.rglob("*.md")
            if f.name not in EXCLUDED_FILENAMES
        ]
    else:
        print(f"❌ Error: Target path '{target_path}' does not exist.", file=sys.stderr)
        return all_findings

    known_sections = collect_sections(files)
    for file_path in sorted(files):
        all_findings.extend(scan_file(file_path, known_sections))
    return all_findings


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        nargs="?",
        default="docs/chapters",
        help="Manuscript directory or single Markdown file to scan",
    )
    args = parser.parse_args(argv)

    target_path = Path(args.target).resolve()
    print(f"🔍 Reviewer-readability scan: {target_path}")

    findings = scan_target(target_path)
    fails = [f for f in findings if f.severity == "FAIL"]
    warns = [f for f in findings if f.severity == "WARN"]

    for f in findings:
        icon = "❌" if f.severity == "FAIL" else "⚠️"
        print(f"  {icon} {f.path.name}:{f.line} [{f.severity}/{f.kind}] '{f.match}' — {f.snippet}")
        print(f"      hint: {HINTS[f.kind]}")

    if fails:
        print(
            f"💥 Reviewer-Readability Check FAILED: {len(fails)} FAIL, {len(warns)} WARN",
            file=sys.stderr,
        )
        return 1

    if warns:
        print(f"⚠️ Reviewer-Readability Check WARN: {len(warns)} item(s) need review (0 FAIL)")
    else:
        print("✅ Reviewer-Readability Check PASSED: prose is free of internal symbols.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
