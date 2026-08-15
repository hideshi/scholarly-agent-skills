# Contributing

Thank you for considering a contribution to Scholarly Agent Skills.

## Before you start

- Keep skills **tool-agnostic**. Do not add Cursor-only, Claude-only, or Antigravity-only instructions unless the host difference is unavoidable and documented.
- Add **both** `skills/ja/` and `skills/en/` for every new skill. Directory names must match.
- Do not commit secrets, personal emails, `.env`, API keys, `mapping.json`, or raw research data.

## Skill quality

Each `SKILL.md` must pass `python3 scripts/check_skill_quality.py`:

- YAML frontmatter with `name`, `version` (semver), and `description`
- `description` includes a trigger (`時` / `when` / `before` / etc.)
- Required sections: `## 目的` or `## Purpose`, and `## 成果物` or `## Outputs`
- `name:` matches the parent directory name
- Relative links must resolve

Run the full suite before opening a pull request:

```bash
python3 scripts/check_skill_quality.py
python3 scripts/run_tests.py
```

## Pull requests

1. Keep the change focused (one skill, one script, or one docs fix).
2. Update `skills/ja/README.md` and `skills/en/README.md` when adding or renaming a skill.
3. Update `CHANGELOG.md` for user-visible changes.
4. Do not include `git add` / `git commit` instructions for end users inside skill bodies unless the skill is explicitly about git workflow.

## Academic integrity / 学術倫理

Generated text is a draft aid. Authors remain responsible for claims, citations, and submissions. Do not add features whose primary purpose is to fabricate sources or bypass scholarly citation practice.

The bilingual disclaimer (Japanese first, then English) is in [DISCLAIMER.md](DISCLAIMER.md). Keep README and AGENTS.md pointers in sync when you change it.
