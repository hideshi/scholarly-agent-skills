#!/usr/bin/env python3
"""
Terminology-Consistency Check for academic paper manuscripts.

Layer 1 (mechanical) of the three-layer terminology consistency system
(skills/ja/terminology-consistency/SKILL.md):

  - variant : a registered non-canonical variant appears in prose -> FAIL
              (the author has already fixed the canonical form; reappearance
              is a regression)
  - gloss   : a glossary English term appears in prose without its Japanese
              counterpart on the same line -> WARN (needs author triage;
              definition sentences "X とは" are exempt)

The bilingual glossary itself is the source of truth — no separate term
dictionary is maintained. Pairs are parsed from Markdown table rows
"| 日本語 | English | ... |" in literature/bilingual-glossary.md (preferred)
or manuscript/appendix-a-glossary.md.

Optional per-paper config: design/sot/terminology-variants.yml

    allowlist:
      - AI
      - DSR
    variants:
      - canonical: 主張の強度
        variants:
          - 主張トーン
        note: Modality の日本語 gloss の統一形

Only the constrained YAML subset above is supported (stdlib-only parser).

Exempt layers (same policy as check_reviewer_readability.py):
tables, blockquotes, code fences, and lines containing
'<!-- terminology:ignore -->'.

Exit codes: 0 = PASS / WARN, 1 = at least one FAIL.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

IGNORE_MARKER = "<!-- terminology:ignore -->"

EXCLUDED_FILENAMES = ("test-cases.md", "evidence-gate-report.md", "references.md")

# Established abbreviations/proper nouns allowed bare even if listed in a glossary.
DEFAULT_ALLOWLIST = {
    "AI", "LLM", "ADHD", "ASD", "Git", "GitHub", "JST", "PDF", "HTML",
    "Markdown", "Mermaid", "YAML", "JSON", "PII", "IRB",
}

HINTS = {
    "variant": "登録済みバリアントです。正準形に統一してください（design/sot/terminology-variants.yml）",
    "gloss": "用語集の英語語が日本語 gloss なしで出現しています。「日本語（English）」形式か、定義文・allowlist への登録を検討してください",
}


@dataclass
class GlossaryTerm:
    ja: str
    en: str  # main English term (trailing "(ABBR)" removed)


@dataclass
class Config:
    allowlist: set = field(default_factory=set)
    variants: List[Tuple[str, List[str], str]] = field(default_factory=list)  # (canonical, [variants], note)


@dataclass
class Finding:
    path: Path
    line: int
    severity: str  # "FAIL" | "WARN"
    kind: str
    match: str
    snippet: str
    hint: str = ""


# ---------------------------------------------------------------- glossary

_ACRO_RE = re.compile(r"\(([^()]*)\)\s*$")
_ACRO_TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9./-]*$")
_EN_ALPHA_RE = re.compile(r"[A-Za-z]{2,}")


def parse_glossary_pairs(text: str) -> Tuple[List[GlossaryTerm], set]:
    """Parse '| 日本語 | English | ... |' rows. Returns (terms, auto_allowlist).

    Trailing parenthetical tokens such as "(EF)" in the English column are
    treated as author-defined abbreviations and auto-allowlisted bare.
    """
    terms: List[GlossaryTerm] = []
    auto_allow: set = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = [c.strip().replace("**", "") for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        ja, en = cells[0], cells[1]
        if ja in ("日本語", "コード") or set(en) <= set(":- "):
            continue
        if not _EN_ALPHA_RE.search(en):
            continue
        m = _ACRO_RE.search(en)
        if m and _ACRO_TOKEN_RE.match(m.group(1)):
            auto_allow.add(m.group(1))
            en = en[: m.start()].strip()
        if ja and en:
            terms.append(GlossaryTerm(ja=ja, en=en))
    return terms, auto_allow


# ---------------------------------------------------------------- config

def load_config(path: Optional[Path]) -> Config:
    """Load the constrained YAML subset (allowlist / variants)."""
    cfg = Config()
    if not path or not path.is_file():
        return cfg
    section: Optional[str] = None
    current: Optional[dict] = None
    in_variants_list = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        body = line.strip()
        if indent == 0:
            section = body.rstrip(":")
            current = None
            in_variants_list = False
            continue
        if section == "allowlist" and body.startswith("- "):
            cfg.allowlist.add(body[2:].strip().strip('"\''))
        elif section == "variants":
            if indent == 2 and body.startswith("- canonical:"):
                current = {
                    "canonical": body.split(":", 1)[1].strip().strip('"\''),
                    "variants": [],
                    "note": "",
                }
                cfg.variants.append((current["canonical"], current["variants"], ""))
                in_variants_list = False
            elif current is not None and indent == 4 and body.startswith("variants:"):
                in_variants_list = True
            elif current is not None and indent == 4 and body.startswith("note:"):
                current["note"] = body.split(":", 1)[1].strip()
                canon, vars_, _ = cfg.variants[-1]
                cfg.variants[-1] = (canon, vars_, current["note"])
            elif current is not None and in_variants_list and body.startswith("- "):
                current["variants"].append(body[2:].strip().strip('"\''))
    return cfg


# ---------------------------------------------------------------- scanning

_GENERIC_GLOSS_RE = re.compile(r"[ぁ-んァ-ヶ一-龥々][（(][^（）()]*$")


def iter_prose_lines(content: str):
    """Yield (line_number, line) excluding tables, blockquotes, code fences.

    Stops at the per-chapter '## 参考文献' section: reference titles are
    verbatim bibliographic data and must not be flagged.
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
        if not stripped or stripped.startswith("|") or stripped.startswith(">"):
            continue
        if IGNORE_MARKER in raw:
            continue
        yield idx, raw


def scan_file(
    file_path: Path,
    terms: List[GlossaryTerm],
    cfg: Config,
    allowlist: set,
) -> List[Finding]:
    findings: List[Finding] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}", file=sys.stderr)
        return findings

    for line_no, raw_line in iter_prose_lines(content):
        line = raw_line.replace("**", "")
        snippet = raw_line.strip()[:80]

        for canonical, variants, note in cfg.variants:
            for variant in variants:
                if variant and variant in line:
                    hint = f"正準形「{canonical}」に統一してください"
                    if note:
                        hint += f"（{note}）"
                    findings.append(Finding(file_path, line_no, "FAIL", "variant", variant, snippet, hint))

        for term in terms:
            if term.en in allowlist:
                continue
            pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(term.en) + r"(?![A-Za-z0-9])")
            for m in pattern.finditer(line):
                before = line[: m.start()]
                after = line[m.end():].lstrip()
                if term.ja and term.ja in before:
                    continue  # glossed on the same line, e.g. 日本語（English）
                if _GENERIC_GLOSS_RE.search(before):
                    continue  # any 日本語（...English...） wrapper, incl. distinct coined terms
                if after.startswith("とは"):
                    continue  # definition sentence
                findings.append(
                    Finding(file_path, line_no, "WARN", "gloss", term.en, snippet, HINTS["gloss"])
                )
    return findings


# ---------------------------------------------------------------- discovery

def _find_upwards(target: Path, rel_candidates: List[str]) -> Optional[Path]:
    for parent in [target, *target.parents][:5]:
        for rel in rel_candidates:
            candidate = parent / rel
            if candidate.is_file():
                return candidate
    return None


def find_glossary(target: Path) -> Optional[Path]:
    return _find_upwards(
        target,
        ["literature/bilingual-glossary.md", "manuscript/appendix-a-glossary.md"],
    )


def find_config(target: Path) -> Optional[Path]:
    return _find_upwards(
        target,
        ["design/sot/terminology-variants.yml", "design/terminology-variants.yml"],
    )


def scan_target(target_path: Path, terms, cfg, allowlist) -> List[Finding]:
    all_findings: List[Finding] = []
    if target_path.is_file():
        files = [target_path]
    elif target_path.is_dir():
        files = [
            f for f in target_path.rglob("*.md")
            if f.name not in EXCLUDED_FILENAMES and "glossary" not in f.name.lower()
        ]
    else:
        print(f"❌ Error: Target path '{target_path}' does not exist.", file=sys.stderr)
        return all_findings
    for file_path in sorted(files):
        all_findings.extend(scan_file(file_path, terms, cfg, allowlist))
    return all_findings


# ---------------------------------------------------------------- main

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        nargs="?",
        default="docs/chapters",
        help="Manuscript directory or single Markdown file to scan",
    )
    parser.add_argument("--glossary", type=Path, default=None, help="Glossary Markdown (SoT)")
    parser.add_argument("--config", type=Path, default=None, help="terminology-variants.yml")
    args = parser.parse_args(argv)

    target_path = Path(args.target).resolve()
    print(f"🔍 Terminology-consistency scan: {target_path}")

    glossary_path = args.glossary or find_glossary(target_path)
    if glossary_path:
        terms, auto_allow = parse_glossary_pairs(glossary_path.read_text(encoding="utf-8"))
        print(f"📖 Glossary (SoT): {glossary_path} ({len(terms)} terms)")
    else:
        terms, auto_allow = [], set()
        print("⚠️ Glossary not found; gloss check disabled (variant check still active)")

    config_path = args.config or find_config(target_path)
    cfg = load_config(config_path)
    if config_path and config_path.is_file():
        print(f"🧭 Config: {config_path} (variants={len(cfg.variants)}, allowlist={len(cfg.allowlist)})")

    allowlist = DEFAULT_ALLOWLIST | auto_allow | cfg.allowlist

    findings = scan_target(target_path, terms, cfg, allowlist)
    fails = [f for f in findings if f.severity == "FAIL"]
    warns = [f for f in findings if f.severity == "WARN"]

    for f in findings:
        icon = "❌" if f.severity == "FAIL" else "⚠️"
        print(f"  {icon} {f.path.name}:{f.line} [{f.severity}/{f.kind}] '{f.match}' — {f.snippet}")
        print(f"      hint: {f.hint}")

    if fails:
        print(
            f"💥 Terminology-Consistency Check FAILED: {len(fails)} FAIL, {len(warns)} WARN",
            file=sys.stderr,
        )
        return 1
    if warns:
        print(f"⚠️ Terminology-Consistency Check WARN: {len(warns)} item(s) need review (0 FAIL)")
    else:
        print("✅ Terminology-Consistency Check PASSED: terminology is consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
