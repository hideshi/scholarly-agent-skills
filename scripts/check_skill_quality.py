#!/usr/bin/env python3
"""
Skill Quality & Frontmatter Validator for Scholarly Agent Skills.
Validates both Japanese (ja) and English (en) skills catalogs.
Uses ONLY Python standard library.

Checks:
  1. YAML frontmatter presence (--- delimiters)
  2. 'name:' and 'description:' field presence
  3. 'name:' field matches parent directory name
  4. Required sections: '## Purpose' or '## 目的'
  5. Output sections: '## Outputs' or '## 成果物'
  6. ja/en skill directory parity (same set of skill directories)
"""

import sys
import re
from pathlib import Path


def validate_skill_file(skill_md_path: Path, expected_dir_name: str = None) -> list[str]:
    errors = []
    if not skill_md_path.exists():
        errors.append(f"Missing SKILL.md file at {skill_md_path}")
        return errors

    content = skill_md_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    if not lines or not lines[0].startswith("---"):
        errors.append("Missing starting YAML frontmatter '---'")

    # Check name field
    name_match = re.search(r'^name:\s*(\S+)', content, flags=re.MULTILINE)
    if not name_match:
        errors.append("Missing or empty 'name:' field in frontmatter")
    elif expected_dir_name and name_match.group(1) != expected_dir_name:
        errors.append(
            f"'name:' field '{name_match.group(1)}' does not match "
            f"directory name '{expected_dir_name}'"
        )

    # Check version field
    version_match = re.search(r'^version:\s*(\S+)', content, flags=re.MULTILINE)
    if not version_match:
        errors.append("Missing or empty 'version:' field in frontmatter")
    elif not re.match(r'^\d+\.\d+\.\d+$', version_match.group(1)):
        errors.append(f"Invalid 'version:' format '{version_match.group(1)}', expected semver (e.g. 1.0.0)")

    # Check description field and trigger condition
    desc_match = re.search(r'^description:\s*(.+)', content, flags=re.MULTILINE)
    if not desc_match or not desc_match.group(1).strip():
        errors.append("Missing or empty 'description:' field in frontmatter")
    else:
        desc_text = desc_match.group(1).lower()
        trigger_keywords = ["時", "場合", "際", "前", "フェーズ", "段階", "when", "before", "during", "after", "use when"]
        if not any(kw in desc_text for kw in trigger_keywords):
            errors.append("'description:' field lacks explicit trigger condition (When). Include keywords like '...時', '...際', 'when...', etc.")

    # Check required sections
    has_purpose = bool(re.search(r'^##\s+(Purpose|目的)', content, flags=re.MULTILINE))
    if not has_purpose:
        errors.append("Missing required section: '## Purpose' or '## 目的'")

    has_outputs = bool(re.search(r'^##\s+(Outputs|成果物|出力)', content, flags=re.MULTILINE))
    if not has_outputs:
        errors.append("Missing recommended section: '## Outputs' or '## 成果物'")

    # Check for empty heading sections (same or higher level heading follows with no content/subheadings)
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
    for i, line in enumerate(lines):
        h_match = heading_pattern.match(line.strip())
        if h_match:
            curr_level = len(h_match.group(1))
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                next_h_match = heading_pattern.match(lines[j].strip())
                if next_h_match:
                    next_level = len(next_h_match.group(1))
                    if next_level <= curr_level:
                        errors.append(f"Empty section heading '{line.strip()}' at line {i + 1}")

    # Remove code blocks before parsing Markdown links
    content_no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    content_no_code = re.sub(r'`[^`\n]+`', '', content_no_code)

    # Check relative Markdown links for existence
    link_matches = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content_no_code)
    for label, target in link_matches:
        target = target.strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        # Strip anchor if present
        target_path_str = target.split("#")[0]
        if not target_path_str:
            continue
        # Only validate local relative path references like ../, ./, scripts/, config/
        if "/" in target_path_str or target_path_str.endswith((".py", ".json", ".md")):
            target_path = (skill_md_path.parent / target_path_str).resolve()
            if not target_path.exists():
                errors.append(f"Broken relative link '[{label}]({target})' -> path '{target_path}' does not exist")

    return errors


def validate_skills_dir(skills_dir: Path) -> tuple[int, int, list[str]]:
    """Validate all skills in a language directory. Returns (count, errors, skill_names)."""
    total_skills = 0
    total_errors = 0
    skill_names = []

    if not skills_dir.exists():
        return 0, 0, []

    print(f"🔍 Validating Scholarly Agent Skills in {skills_dir}...")
    for skill_path in sorted(skills_dir.iterdir()):
        if skill_path.is_dir() and skill_path.name not in ('ja', 'en'):
            total_skills += 1
            skill_names.append(skill_path.name)
            skill_md = skill_path / "SKILL.md"
            errors = validate_skill_file(skill_md, expected_dir_name=skill_path.name)
            if errors:
                total_errors += len(errors)
                print(f"❌ [{skill_path.name}] Validation failed:")
                for err in errors:
                    print(f"   - {err}")
            else:
                print(f"  ✅ [{skill_path.name}] SKILL.md valid")

    return total_skills, total_errors, skill_names


def validate_lang_parity(skills_root: Path) -> int:
    """Check that ja and en directories contain the same set of skill directories."""
    ja_dir = skills_root / "ja"
    en_dir = skills_root / "en"

    if not ja_dir.exists() or not en_dir.exists():
        return 0

    ja_skills = {d.name for d in sorted(ja_dir.iterdir()) if d.is_dir()}
    en_skills = {d.name for d in sorted(en_dir.iterdir()) if d.is_dir()}

    parity_errors = 0

    ja_only = ja_skills - en_skills
    en_only = en_skills - ja_skills

    if ja_only:
        parity_errors += len(ja_only)
        print(f"\n⚠️  Skills present in ja/ but missing in en/: {', '.join(sorted(ja_only))}")
    if en_only:
        parity_errors += len(en_only)
        print(f"\n⚠️  Skills present in en/ but missing in ja/: {', '.join(sorted(en_only))}")

    if not ja_only and not en_only:
        print(f"\n✅ ja/en skill directory parity check passed ({len(ja_skills)} skills each)")

    return parity_errors


def main():
    repo_root = Path(__file__).parent.parent
    skills_root = repo_root / "skills"

    if not skills_root.exists():
        print(f"❌ Skills directory not found at {skills_root}", file=sys.stderr)
        sys.exit(1)

    total_skills = 0
    total_errors = 0

    # Validate ja and en subdirectories if they exist
    for lang in ["ja", "en"]:
        lang_dir = skills_root / lang
        if lang_dir.exists():
            s_count, e_count, _ = validate_skills_dir(lang_dir)
            total_skills += s_count
            total_errors += e_count

    # Also check root skills/ if skills exist directly
    r_count, re_count, _ = validate_skills_dir(skills_root)
    total_skills += r_count
    total_errors += re_count

    # Check ja/en parity
    parity_errors = validate_lang_parity(skills_root)
    total_errors += parity_errors

    if total_errors == 0:
        print(f"\n🎉 All {total_skills} skills across languages passed validation!")
        sys.exit(0)
    else:
        print(f"\n💥 Validation failed with {total_errors} error(s).", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
