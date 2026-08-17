#!/usr/bin/env python3
"""
Pre-submission gate for academic paper repositories.

Runs a fixed set of mechanical checks against a paper under docs/<paper-id>/.
Designed to be a mandatory gate before manuscript build / submission.

Checks:
  1. check_output_boundary.py  — internal workflow terms must not leak into chapters/
  2. check_fact_grounding.py   — quantitative candidate paragraphs must have anchors
  3. check_citation_format.py  — citations must be registered in literature-matrix.md
  4. check_literature_grounding.py — citations must have literature/papers/*.md artifacts

Exit codes:
  0 = all checks pass (WARN allowed unless --strict-warn)
  1 = at least one FAIL / error, or WARN with --strict-warn
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

SCRIPTS_DIR = Path(__file__).resolve().parent


@dataclass
class CheckResult:
    name: str
    ok: bool
    warn: bool
    output: str


def run_check(name: str, cmd: List[str], cwd: Path) -> CheckResult:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    out = (res.stdout or "") + (("\n" + res.stderr) if res.stderr else "")
    out = out.strip()
    # WARN heuristics: scripts print WARN/⚠️ lines but may still exit 0
    warn = ("WARN" in out) or ("⚠️" in out)
    ok = res.returncode == 0
    return CheckResult(name=name, ok=ok, warn=warn, output=out)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper_id", help="Paper ID under docs/<paper-id>/")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing docs/ (default: cwd)",
    )
    parser.add_argument(
        "--strict-warn",
        action="store_true",
        help="Treat WARN as failure (exit 1)",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    base = repo_root / "docs" / args.paper_id
    chapters = base / "chapters"
    papers_dir = base / "literature" / "papers"
    matrix = base / "literature" / "literature-matrix.md"

    if not chapters.is_dir():
        print(f"Error: chapters directory not found: {chapters}", file=sys.stderr)
        return 1

    checks: List[tuple[str, List[str]]] = [
        (
            "output-boundary",
            [sys.executable, str(SCRIPTS_DIR / "check_output_boundary.py"), str(chapters)],
        ),
        (
            "fact-grounding",
            [
                sys.executable,
                str(SCRIPTS_DIR / "check_fact_grounding.py"),
                str(chapters),
            ],
        ),
        (
            "citation-format",
            [
                sys.executable,
                str(SCRIPTS_DIR / "check_citation_format.py"),
                str(chapters),
                "--matrix",
                str(matrix),
            ],
        ),
        (
            "literature-grounding",
            [
                sys.executable,
                str(SCRIPTS_DIR / "check_literature_grounding.py"),
                str(chapters),
                "--papers-dir",
                str(papers_dir),
                "--matrix",
                str(matrix),
            ],
        ),
    ]

    results: List[CheckResult] = []
    for name, cmd in checks:
        results.append(run_check(name, cmd, repo_root))

    print(f"🧪 Pre-submission gate: {args.paper_id}")
    print(f"   repo: {repo_root}")
    print(f"   chapters: {chapters}")
    print()

    any_fail = False
    any_warn = False
    for r in results:
        icon = "✅" if r.ok and not r.warn else ("⚠️" if r.ok else "❌")
        status = "PASS" if r.ok and not r.warn else ("WARN" if r.ok else "FAIL")
        print(f"{icon} {r.name}: {status}")
        any_fail = any_fail or not r.ok
        any_warn = any_warn or r.warn

    print()
    for r in results:
        if not r.ok or r.warn:
            print(f"===== {r.name} =====")
            print(r.output[:8000])
            print()

    if any_fail:
        print("💥 Pre-submission gate FAILED.")
        return 1
    if args.strict_warn and any_warn:
        print("💥 Pre-submission gate FAILED (strict-warn).")
        return 1

    print("✅ Pre-submission gate PASSED" + (" (with WARN)" if any_warn else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
