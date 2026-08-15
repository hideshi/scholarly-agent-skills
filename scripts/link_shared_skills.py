#!/usr/bin/env python3
"""
Python script to link shared skills and rules to a target project directory.
Supports Cursor (.cursor/), Claude Code (.claude/), and Generic Agents (.agents/).
Supports language selection (--lang ja | en). Default is 'ja'.
Uses ONLY Python standard library.
"""

import sys
import argparse
from pathlib import Path

def link_shared_skills(target_dir: Path, lang: str = "ja") -> bool:
    target_dir = target_dir.resolve()
    repo_dir = Path(__file__).parent.parent.resolve()
    
    skills_src = repo_dir / "skills" / lang
    rules_src = repo_dir / "rules" / lang
    
    if not skills_src.exists():
        # Fallback to root skills/ if lang subdir doesn't exist
        skills_src = repo_dir / "skills"
    if not rules_src.exists():
        # Fallback to root rules/ if lang subdir doesn't exist
        rules_src = repo_dir / "rules"
        
    print(f"🔗 Linking Scholarly Agent Skills (lang: {lang}) to {target_dir}...")
    
    (target_dir / ".cursor").mkdir(parents=True, exist_ok=True)
    (target_dir / ".claude").mkdir(parents=True, exist_ok=True)
    (target_dir / ".agents").mkdir(parents=True, exist_ok=True)
    
    agents_md_src = repo_dir / f"AGENTS.{lang}.md" if (repo_dir / f"AGENTS.{lang}.md").exists() else repo_dir / "AGENTS.md"
    claude_md_src = repo_dir / f"CLAUDE.{lang}.md" if (repo_dir / f"CLAUDE.{lang}.md").exists() else repo_dir / "CLAUDE.md"
    
    links = [
        (target_dir / "skills", skills_src),
        (target_dir / "rules", rules_src),
        (target_dir / ".cursor" / "skills", skills_src),
        (target_dir / ".cursor" / "rules", rules_src),
        (target_dir / ".claude" / "skills", skills_src),
        (target_dir / ".agents" / "skills", skills_src),
        (target_dir / "AGENTS.md", agents_md_src),
        (target_dir / "CLAUDE.md", claude_md_src),
    ]
    
    for link_path, src_target in links:
        if link_path.is_symlink() or link_path.exists():
            try:
                link_path.unlink()
            except Exception as e:
                print(f"Warning: Could not remove {link_path}: {e}", file=sys.stderr)
                
        try:
            link_path.symlink_to(src_target)
            print(f"  ✅ Linked {link_path.name} -> {src_target}")
        except Exception as e:
            print(f"  ❌ Failed to link {link_path}: {e}", file=sys.stderr)
            return False
            
    print(f"✅ Successfully linked skills and rules (lang: {lang}) to {target_dir}!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Link shared skills and rules to a target project directory.")
    parser.add_argument("target", help="Target project directory path")
    parser.add_argument("--lang", choices=["ja", "en"], default="ja", help="Skill language (ja or en, default: ja)")
    args = parser.parse_args()
    
    target_path = Path(args.target)
    if not target_path.exists():
        print(f"Error: Target directory '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    success = link_shared_skills(target_path, lang=args.lang)
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
