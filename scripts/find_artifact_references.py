#!/usr/bin/env python3
"""
Extract references to artifact files under a target directory
(e.g., docs/<paper-id>/design/).

Use cases (artifact-index-rule.md):
  - BEFORE migration (HITL): present the impact scope of moving artifacts
    into category directories (sot/, proposals/, briefs/, ...).
  - AFTER migration (--stale-only): detect references that still point to
    the pre-migration flat layout (e.g., `design/foo.md` when the file now
    lives at `design/sot/foo.md`).

Exit codes: 0 = completed (informational tool; no pass/fail semantics).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

MD_GLOB = "*.md"
EXCLUDE_DIR_NAMES = {".git", "node_modules", "__pycache__", "raw_data"}


@dataclass
class Reference:
    referrer: Path
    lineno: int
    line: str
    kind: str  # markdown-link | inline-path | bare-name


def collect_artifacts(target_dir: Path) -> List[Path]:
    return sorted(p for p in target_dir.rglob(MD_GLOB) if p.is_file())


def iter_search_files(search_root: Path) -> List[Path]:
    files: List[Path] = []
    for path in search_root.rglob(MD_GLOB):
        if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def build_patterns(artifact: Path, target_dir: Path) -> List[tuple[re.Pattern[str], str]]:
    """Patterns that may refer to the artifact, most specific first."""
    name = artifact.name
    rel_to_parent = f"{target_dir.name}/{name}"  # flat-layout path, e.g. design/foo.md
    patterns: List[tuple[re.Pattern[str], str]] = [
        (re.compile(r"\]\([^)]*" + re.escape(name) + r"\)"), "markdown-link"),
        (re.compile(re.escape(rel_to_parent) + r"\b"), "inline-path"),
        (re.compile(re.escape(name)), "bare-name"),
    ]
    return patterns


def find_references(
    artifact: Path,
    target_dir: Path,
    search_files: List[Path],
    exclude_self: bool,
) -> List[Reference]:
    refs: List[Reference] = []
    patterns = build_patterns(artifact, target_dir)
    for referrer in search_files:
        if exclude_self and referrer == artifact:
            continue
        try:
            lines = referrer.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, start=1):
            for pattern, kind in patterns:
                if pattern.search(line):
                    refs.append(Reference(referrer, lineno, line.strip(), kind))
                    break
    return refs


def is_stale(line: str, artifact: Path, target_dir: Path) -> bool:
    """True if the line cites the flat-layout path (target_dir.name/name)
    while the artifact actually lives in a subdirectory."""
    if artifact.parent == target_dir:
        return False  # not migrated into a subdirectory
    flat_path = f"{target_dir.name}/{artifact.name}"
    nested = f"{target_dir.name}/{artifact.parent.name}/{artifact.name}"
    return flat_path in line and nested not in line


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target_dir", type=Path, help="Artifact directory (e.g. docs/<paper-id>/design)")
    parser.add_argument(
        "--search-root",
        type=Path,
        default=None,
        help="Root to search references from (default: repository root = target_dir's docs/ parent, else cwd)",
    )
    parser.add_argument(
        "--stale-only",
        action="store_true",
        help="Report only references to the pre-migration flat layout",
    )
    parser.add_argument(
        "--exclude",
        type=Path,
        action="append",
        default=[],
        help="Referrer paths to exclude (e.g. historical logs); repeatable",
    )
    args = parser.parse_args(argv)

    target_dir = args.target_dir.resolve()
    if not target_dir.is_dir():
        print(f"ERROR: target_dir not found: {target_dir}", file=sys.stderr)
        return 2

    search_root = args.search_root.resolve() if args.search_root else _default_search_root(target_dir)
    excluded: Set[Path] = {p.resolve() for p in args.exclude}

    artifacts = collect_artifacts(target_dir)
    search_files = [p for p in iter_search_files(search_root) if p not in excluded]

    total = 0
    for artifact in artifacts:
        refs = find_references(artifact, target_dir, search_files, exclude_self=True)
        if args.stale_only:
            refs = [r for r in refs if is_stale(r.line, artifact, target_dir)]
        if not refs:
            continue
        rel_artifact = artifact.relative_to(target_dir)
        print(f"\n## {rel_artifact}")
        for ref in refs:
            rel_referrer = ref.referrer.relative_to(search_root)
            print(f"  - {rel_referrer}:{ref.lineno} [{ref.kind}] {ref.line[:120]}")
            total += 1

    mode = "stale (flat-layout) references" if args.stale_only else "references"
    print(f"\n{total} {mode} found across {len(artifacts)} artifacts under {target_dir}")
    return 0


def _default_search_root(target_dir: Path) -> Path:
    for parent in target_dir.parents:
        if parent.name == "docs":
            return parent.parent
    return Path.cwd()


if __name__ == "__main__":
    sys.exit(main())
