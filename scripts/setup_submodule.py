#!/usr/bin/env python3
"""
Python script to setup Agent links when scholarly-agent-skills is added as a Git Submodule.
Supports language selection (--lang ja | en). Default is 'ja'.
Uses ONLY Python standard library.
Run this script from the root of your target paper repository.
"""

import sys
import os
import argparse
from pathlib import Path

def setup_submodule_links(target_dir: Path = None, lang: str = "ja") -> bool:
    if target_dir is None:
        target_dir = Path.cwd().resolve()
    else:
        target_dir = target_dir.resolve()
        
    submodule_dir = Path(__file__).parent.parent.resolve()
    
    if submodule_dir == target_dir:
        print("⚠️ Warning: This script is intended to be run inside a parent paper repository containing scholarly-agent-skills as a submodule.", file=sys.stderr)
        print("Usage inside your paper repository:", file=sys.stderr)
        print("  git submodule add <repo-url> .scholarly-agent-skills", file=sys.stderr)
        print("  python3 .scholarly-agent-skills/scripts/setup_submodule.py [--lang ja|en]", file=sys.stderr)
        return False
        
    print(f"📦 Setting up Submodule Agent links (lang: {lang}) in {target_dir}...")
    
    # Calculate relative path from target_dir to submodule_dir
    rel_submodule = os.path.relpath(submodule_dir, target_dir)
    
    # Check language subdirectory presence
    skills_sub = f"skills/{lang}" if (submodule_dir / "skills" / lang).exists() else "skills"
    rules_sub = f"rules/{lang}" if (submodule_dir / "rules" / lang).exists() else "rules"
    
    agents_file = f"AGENTS.{lang}.md" if (submodule_dir / f"AGENTS.{lang}.md").exists() else "AGENTS.md"
    claude_file = f"CLAUDE.{lang}.md" if (submodule_dir / f"CLAUDE.{lang}.md").exists() else "CLAUDE.md"
    
    # Ensure target subdirectories exist
    (target_dir / ".cursor").mkdir(parents=True, exist_ok=True)
    (target_dir / ".claude").mkdir(parents=True, exist_ok=True)
    (target_dir / ".agents").mkdir(parents=True, exist_ok=True)
    
    links_to_create = [
        (target_dir / "skills", os.path.join(rel_submodule, skills_sub)),
        (target_dir / "rules", os.path.join(rel_submodule, rules_sub)),
        (target_dir / ".cursor" / "skills", os.path.join(rel_submodule, skills_sub)),
        (target_dir / ".cursor" / "rules", os.path.join(rel_submodule, rules_sub)),
        (target_dir / ".claude" / "skills", os.path.join(rel_submodule, skills_sub)),
        (target_dir / ".agents" / "skills", os.path.join(rel_submodule, skills_sub)),
        (target_dir / "AGENTS.md", os.path.join(rel_submodule, agents_file)),
        (target_dir / "CLAUDE.md", os.path.join(rel_submodule, claude_file)),
    ]
    
    for link_path, target_rel in links_to_create:
        if link_path.is_symlink() or link_path.exists():
            try:
                link_path.unlink()
            except Exception as e:
                print(f"Warning: Could not remove existing file {link_path}: {e}", file=sys.stderr)
                
        try:
            link_path.symlink_to(target_rel)
            print(f"  ✅ Linked {link_path.relative_to(target_dir)} -> {target_rel}")
        except Exception as e:
            print(f"  ❌ Failed to link {link_path}: {e}", file=sys.stderr)
            return False
            
    print(f"🎉 Successfully configured Git Submodule Agent links (lang: {lang})!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Configure Git Submodule Agent links in parent repository.")
    parser.add_argument("--target", "-t", help="Target paper repository directory (defaults to current working directory)")
    parser.add_argument("--lang", choices=["ja", "en"], default="ja", help="Skill language (ja or en, default: ja)")
    args = parser.parse_args()
    
    target_path = Path(args.target) if args.target else Path.cwd()
    success = setup_submodule_links(target_path, lang=args.lang)
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
