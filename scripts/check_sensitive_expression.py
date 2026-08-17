#!/usr/bin/env python3
"""
Sensitive-Expression Check for academic paper manuscripts.

Layer 1 (mechanical) of the three-layer sensitive-expression guard system
(skills/ja/sensitive-expression-guard/SKILL.md). Designed primarily for
self-referential DSR papers, where careless readers may short-circuit
symptom-adjacent vocabulary into misidentifying the author's medical
status, or rhetorical absolutes may exceed the declared modality ceiling.

Rule categories (all WARN unless noted):

  - absolute     : unbounded quantifiers/rhetorical absolutes (無尽蔵, すべて…)
  - quantifier   : vague population quantifiers (少なくない, 多くの…) —
                   exempt when the same line carries a citation year
  - modality     : flagged claim verbs (解明する, 証明する…) —
                   exempt on lines mentioning 将来/課題 (future work)
  - deficit      : deficit-model vocabulary (障害, 患者…)
  - misidentify  : a medicalizing term co-occurs with an author
                   self-reference in the same paragraph AND the paragraph
                   carries no disclaimer pattern
  - abstract     : terms restricted from the abstract register
                   (abstract is extracted from design/sot/paper-outline.md)
  - disclaimer   : presence requirement — if any medicalizing term is used
                   at all, a non-diagnostic disclaimer pattern must exist
                   somewhere in the scanned prose
  - banned       : author-registered regressions -> FAIL

Per-line suppression: '<!-- sensitive:ignore -->'. Tables, blockquotes and
code fences are exempt (same policy as check_reviewer_readability.py).

Optional per-paper config: design/sot/sensitive-expressions.yml — lists are
UNIONED with the built-in defaults. Allowlist entries are either
"term" (suppress globally) or "term|context" (suppress when the line also
contains the context substring, e.g. meta-discussion of the term).

Exit codes: 0 = PASS / WARN, 1 = at least one FAIL (banned term).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

IGNORE_MARKER = "<!-- sensitive:ignore -->"

# ------------------------------------------------------------------ defaults

DEFAULT_ABSOLUTE = ["無尽蔵", "すべての", "全ての", "完全に", "絶対に", "常に", "一切"]
DEFAULT_QUANTIFIER = ["少なくない", "多くの", "ほとんど", "一般的に", "大半の"]
DEFAULT_MODALITY_FLAGGED = ["解明する", "証明する", "明らかにする", "実証する", "立証する"]
MODALITY_EXEMPT_SUBSTRINGS = ["将来", "課題", "委ね"]
DEFAULT_DEFICIT = ["障害", "患者", "症候群"]
DEFAULT_MEDICALIZING = ["ADHD", "診断", "スペクトラム", "疾患", "病理"]
DEFAULT_SELF_REFERENCE = ["著者自身", "著者本人", "著者は", "自己言及"]
DEFAULT_DISCLAIMER_PATTERNS = [
    r"診断の有無を問わ",
    r"診断され(てい|て)ない",
    r"病理としてではなく",
    r"病理に限定せず",
    r"推定・分類する用途を想定しない",
]

# Negation cues: a flagged term inside a negated sentence is the paper's
# DEFENSE (non-claim / limitation), not a violation. "せず" is deliberately
# excluded: it appears in subordinate defense clauses (「病理に限定せず…
# 広く見られる」) whose main clause may still carry an ungrounded claim.
# Clause-level attribution is left to the LLM triage layer (skill).
NEGATION_CUES = ["ではな", "わけで", "ものでは", "えない", "できない"]
DEFAULT_ABSTRACT_FLAGGED = ["スペクトラム"]
DEFAULT_BANNED: List[str] = []

HINTS = {
    "absolute": "絶対・無限量詞です。検証可能な範囲の表現に較正してください",
    "quantifier": "定性的な集団量詞です。引用を添えるか、存在主語の表現に弱めてください",
    "modality": "宣言された主張強度の天井を超える可能性のある動詞です。§2.5 系の限定と整合させてください",
    "deficit": "欠陥モデル語彙です。神経多様性の立場と整合するか確認してください",
    "misidentify": "医学化語彙と著者自己言及が同段落に共起しています。読者が著者の診断状態を誤認するリスクがあります",
    "abstract": "アブストラクトでは使用を避ける方針の語です（本文では定義付きで使用可）",
    "disclaimer": "医学化語彙を使用する論文には非診断カテゴリ宣言の一文が必要です",
    "banned": "著者確定済みの禁止表現が再出現しています（回帰）",
}

_ABSTRACT_RE = re.compile(r"## 1\. アブストラクト[^\n]*\n+(.*?)\n---", re.DOTALL)
_CITATION_YEAR_RE = re.compile(r"[（(\[][^（）()\[\]]*(19|20)\d{2}[^（）()\[\]]*[）)\]]")


@dataclass
class Config:
    absolute: List[str] = field(default_factory=list)
    quantifier: List[str] = field(default_factory=list)
    modality_flagged: List[str] = field(default_factory=list)
    deficit: List[str] = field(default_factory=list)
    medicalizing: List[str] = field(default_factory=list)
    self_reference: List[str] = field(default_factory=list)
    disclaimer_patterns: List[str] = field(default_factory=list)
    abstract_flagged: List[str] = field(default_factory=list)
    banned: List[str] = field(default_factory=list)
    allowlist: List[Tuple[str, Optional[str]]] = field(default_factory=list)  # (term, context)


@dataclass
class Finding:
    source: str  # file name or "abstract"
    line: int
    severity: str  # "FAIL" | "WARN"
    kind: str
    match: str
    snippet: str
    hint: str = ""


# -------------------------------------------------------------------- config

_SECTION_MAP = {
    "absolute_terms": "absolute",
    "quantifier_terms": "quantifier",
    "modality_flagged": "modality_flagged",
    "deficit_model_terms": "deficit",
    "medicalizing_terms": "medicalizing",
    "self_reference_terms": "self_reference",
    "disclaimer_patterns": "disclaimer_patterns",
    "abstract_flagged": "abstract_flagged",
    "banned_terms": "banned",
}


def load_config(path: Optional[Path]) -> Config:
    """Load the constrained YAML subset (flat sections of '- item' lists)."""
    cfg = Config()
    if not path or not path.is_file():
        return cfg
    section: Optional[str] = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        body = line.strip()
        if indent == 0:
            section = body.rstrip(":")
            continue
        if not body.startswith("- "):
            continue
        value = body[2:].strip().strip('"\'')
        if section == "allowlist":
            if "|" in value:
                term, context = value.split("|", 1)
                cfg.allowlist.append((term.strip(), context.strip()))
            else:
                cfg.allowlist.append((value, None))
        elif section in _SECTION_MAP:
            getattr(cfg, _SECTION_MAP[section]).append(value)
    return cfg


# ------------------------------------------------------------------- scanning

def iter_prose_blocks(content: str):
    """Yield (line_number, line) excluding tables/blockquotes/fences, but
    PRESERVING blank lines (paragraph boundaries matter for co-occurrence).

    Stops at the per-chapter '## 参考文献' section (verbatim bibliography).
    """
    in_fence = False
    for idx, raw in enumerate(content.splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("## 参考文献"):
            break
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            yield idx, ""
            continue
        if stripped.startswith("|") or stripped.startswith(">"):
            continue
        if IGNORE_MARKER in raw:
            continue
        yield idx, raw


def _allowlisted(term: str, line: str, allowlist: List[Tuple[str, Optional[str]]]) -> bool:
    for entry, context in allowlist:
        if entry != term:
            continue
        if context is None or context in line:
            return True
    return False


def _mentioned(term: str, line: str) -> bool:
    """Mention-vs-use: a term enclosed in 「」 is being discussed, not used."""
    return f"「{term}」" in line


def _negated(line: str) -> bool:
    return any(cue in line for cue in NEGATION_CUES)


def _iter_paragraphs(lines: List[Tuple[int, str]]):
    """Group prose lines into (start_line, text) paragraphs (blank-line split)."""
    buf: List[str] = []
    start = 0
    for line_no, text in lines:
        if text.strip():
            if not buf:
                start = line_no
            buf.append(text)
        elif buf:
            yield start, "\n".join(buf)
            buf = []
    if buf:
        yield start, "\n".join(buf)


def scan_lines(
    source: str,
    lines: List[Tuple[int, str]],
    cfg: Config,
    scope: str = "body",
) -> Tuple[List[Finding], bool, bool]:
    """Scan prose lines. Returns (findings, saw_medicalizing, saw_disclaimer)."""
    findings: List[Finding] = []
    saw_med = False
    saw_disclaimer = False

    absolute = DEFAULT_ABSOLUTE + cfg.absolute
    quantifier = DEFAULT_QUANTIFIER + cfg.quantifier
    modality = DEFAULT_MODALITY_FLAGGED + cfg.modality_flagged
    deficit = DEFAULT_DEFICIT + cfg.deficit
    medicalizing = DEFAULT_MEDICALIZING + cfg.medicalizing
    self_ref = DEFAULT_SELF_REFERENCE + cfg.self_reference
    disclaimers = [re.compile(p) for p in (DEFAULT_DISCLAIMER_PATTERNS + cfg.disclaimer_patterns)]
    abstract_flagged = DEFAULT_ABSTRACT_FLAGGED + cfg.abstract_flagged
    banned = DEFAULT_BANNED + cfg.banned

    for line_no, raw in lines:
        line = raw.replace("**", "")
        snippet = raw.strip()[:80]

        if any(p.search(line) for p in disclaimers):
            saw_disclaimer = True
        if any(t in line for t in medicalizing):
            saw_med = True

        def add(severity: str, kind: str, term: str) -> None:
            findings.append(Finding(source, line_no, severity, kind, term, snippet, HINTS[kind]))

        for term in banned:
            if term and term in line and not _allowlisted(term, line, cfg.allowlist):
                add("FAIL", "banned", term)
        for term in absolute:
            if term and term in line and not _allowlisted(term, line, cfg.allowlist):
                if _negated(line) or _mentioned(term, line):
                    continue  # the sentence IS the defense (non-claim / mention)
                add("WARN", "absolute", term)
        for term in quantifier:
            if term and term in line and not _allowlisted(term, line, cfg.allowlist):
                if _CITATION_YEAR_RE.search(line):
                    continue  # grounded by an on-line citation
                if _negated(line) or _mentioned(term, line):
                    continue
                add("WARN", "quantifier", term)
        for term in modality:
            if term and term in line and not _allowlisted(term, line, cfg.allowlist):
                if any(x in line for x in MODALITY_EXEMPT_SUBSTRINGS):
                    continue  # future-work framing
                if _negated(line) or _mentioned(term, line):
                    continue
                add("WARN", "modality", term)
        for term in deficit:
            if term and term in line and not _allowlisted(term, line, cfg.allowlist):
                if _negated(line) or _mentioned(term, line):
                    continue
                add("WARN", "deficit", term)
        if scope == "abstract":
            for term in abstract_flagged:
                if term and term in line and not _allowlisted(term, line, cfg.allowlist):
                    add("WARN", "abstract", term)

    for start, para in _iter_paragraphs(lines):
        med_hit = next((t for t in medicalizing if t and t in para), None)
        ref_hit = next((t for t in self_ref if t and t in para), None)
        if med_hit and ref_hit and not any(p.search(para) for p in disclaimers):
            snippet = para.replace("\n", " ")[:80]
            findings.append(
                Finding(source, start, "WARN", "misidentify", f"{ref_hit}×{med_hit}", snippet, HINTS["misidentify"])
            )

    return findings, saw_med, saw_disclaimer


def extract_abstract_lines(outline: Path) -> List[Tuple[int, str]]:
    """Extract (line_no, text) pairs from the outline's abstract section."""
    text = outline.read_text(encoding="utf-8")
    m = _ABSTRACT_RE.search(text)
    if not m:
        return []
    base = text[: m.start(1)].count("\n")
    result = []
    for i, line in enumerate(m.group(1).splitlines(), start=1):
        if line.strip():
            result.append((base + i, line))
    return result


# ------------------------------------------------------------------ discovery

def _find_upwards(target: Path, rel_candidates: List[str]) -> Optional[Path]:
    for parent in [target, *target.parents][:5]:
        for rel in rel_candidates:
            candidate = parent / rel
            if candidate.is_file():
                return candidate
    return None


def find_config(target: Path) -> Optional[Path]:
    return _find_upwards(
        target,
        ["design/sot/sensitive-expressions.yml", "design/sensitive-expressions.yml"],
    )


def find_outline(target: Path) -> Optional[Path]:
    return _find_upwards(target, ["design/sot/paper-outline.md"])


def gather_prose(target_path: Path) -> List[Tuple[str, List[Tuple[int, str]]]]:
    """Collect prose lines per chapter file."""
    if target_path.is_file():
        files = [target_path]
    else:
        files = sorted(target_path.rglob("*.md"))
    units = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
        except Exception as e:
            print(f"⚠️ Error reading {f}: {e}", file=sys.stderr)
            continue
        units.append((f.name, list(iter_prose_blocks(content))))
    return units


# ----------------------------------------------------------------------- main

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        nargs="?",
        default="docs/chapters",
        help="Chapter directory or single Markdown file to scan",
    )
    parser.add_argument("--config", type=Path, default=None, help="sensitive-expressions.yml")
    parser.add_argument("--outline", type=Path, default=None, help="paper-outline.md (abstract scope)")
    args = parser.parse_args(argv)

    target_path = Path(args.target).resolve()
    print(f"🔍 Sensitive-expression scan: {target_path}")

    config_path = args.config or find_config(target_path)
    cfg = load_config(config_path)
    if config_path and config_path.is_file():
        print(f"🧭 Config: {config_path}")

    findings: List[Finding] = []
    saw_med = False
    saw_disclaimer = False

    for name, lines in gather_prose(target_path):
        f, med, disc = scan_lines(name, lines, cfg, scope="body")
        findings.extend(f)
        saw_med |= med
        saw_disclaimer |= disc

    outline_path = args.outline or find_outline(target_path)
    if outline_path and Path(outline_path).is_file():
        abstract_lines = extract_abstract_lines(outline_path)
        if abstract_lines:
            f, med, disc = scan_lines(
                f"{outline_path.name}#abstract", abstract_lines, cfg, scope="abstract"
            )
            findings.extend(f)
            saw_med |= med
            saw_disclaimer |= disc
    else:
        print("⚠️ paper-outline.md not found; abstract-register check skipped")

    if saw_med and not saw_disclaimer:
        findings.append(
            Finding("(paper)", 0, "WARN", "disclaimer", "—", "医学化語彙の使用に対し非診断宣言が見つかりません", HINTS["disclaimer"])
        )

    fails = [f for f in findings if f.severity == "FAIL"]
    warns = [f for f in findings if f.severity == "WARN"]

    for f in findings:
        icon = "❌" if f.severity == "FAIL" else "⚠️"
        print(f"  {icon} {f.source}:{f.line} [{f.severity}/{f.kind}] '{f.match}' — {f.snippet}")
        print(f"      hint: {f.hint}")

    if fails:
        print(
            f"💥 Sensitive-Expression Check FAILED: {len(fails)} FAIL, {len(warns)} WARN",
            file=sys.stderr,
        )
        return 1
    if warns:
        print(f"⚠️ Sensitive-Expression Check WARN: {len(warns)} item(s) need triage (0 FAIL)")
    else:
        print("✅ Sensitive-Expression Check PASSED: no risky expressions detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
