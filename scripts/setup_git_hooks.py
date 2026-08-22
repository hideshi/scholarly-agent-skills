#!/usr/bin/env python3
"""
Enable versioned Git hooks for this scholarly-agent-skills clone.

Sets core.hooksPath to .githooks/ so pre-push runs the same checks as CI.
Uses ONLY Python standard library. Does not commit.
"""

import argparse
import stat
import subprocess
import sys
from pathlib import Path


HOOKS_DIRNAME = ".githooks"
PRE_PUSH_NAME = "pre-push"


def _run_git(repo_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def setup_git_hooks(repo_dir: Path) -> bool:
    repo_dir = repo_dir.resolve()
    hooks_dir = repo_dir / HOOKS_DIRNAME
    pre_push = hooks_dir / PRE_PUSH_NAME

    if not (repo_dir / ".git").exists():
        print(f"Error: '{repo_dir}' is not a Git repository.", file=sys.stderr)
        return False

    if not pre_push.is_file():
        print(f"Error: missing hook file '{pre_push}'.", file=sys.stderr)
        return False

    pre_push.chmod(pre_push.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    result = _run_git(repo_dir, "config", "core.hooksPath", HOOKS_DIRNAME)
    if result.returncode != 0:
        print(result.stderr.strip() or f"Error: git config failed in '{repo_dir}'.", file=sys.stderr)
        return False

    verify = _run_git(repo_dir, "config", "--get", "core.hooksPath")
    hooks_path = (verify.stdout or "").strip()
    if verify.returncode != 0 or hooks_path != HOOKS_DIRNAME:
        print(
            f"Error: core.hooksPath is '{hooks_path}', expected '{HOOKS_DIRNAME}'.",
            file=sys.stderr,
        )
        return False

    print(f"🔒 Git hooks enabled in {repo_dir}")
    print(f"  ✅ core.hooksPath = {HOOKS_DIRNAME}")
    print(f"  ✅ {HOOKS_DIRNAME}/{PRE_PUSH_NAME} is executable")
    print("  ℹ️  git push now runs scripts/run_tests.py and scripts/check_skill_quality.py")
    print("  ℹ️  Emergency bypass: git push --no-verify")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Point this clone at .githooks/ so pre-push matches GitHub CI."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="scholarly-agent-skills repository root (defaults to current directory)",
    )
    args = parser.parse_args()

    success = setup_git_hooks(Path(args.target))
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
