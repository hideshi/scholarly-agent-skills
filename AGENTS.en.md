# AGENTS.md — Scholarly Agent Skills & Rules Engine

> **Universal Entry Point for AI Agents (Claude Code, OpenAI Codex, Cursor, Antigravity, etc.)**

This document serves as the universal system entry point for AI agents operating on this repository.

## 免責事項 / Disclaimer

Full text: [`DISCLAIMER.md`](DISCLAIMER.md) (Japanese first, then English). Agents must follow the points below.

- 本スキル集は無保証の支援ツールである。生成文・出典・投稿の正確性は保証しない。
- 品質ゲートを通しても誤りは残り得る。確定情報として述べない。
- 提出先案内は現行規定の確認を利用者に求める。投稿可否を断定しない。
- 研究倫理・PII・IRB・著作権・外部API規約は利用者の責任である。エージェントは適法性を保証しない。
- 法律・医療・投資その他の専門助言をしない。
- 免責を省略したり、「問題ないので投稿してよい」と保証したりしない。

- This repository is an as-is aid. Do not claim that generated text, citations, or venue advice are guaranteed correct.
- Quality gates can miss errors. Ask the user to verify primary sources.
- Research ethics, PII, copyright, and API terms remain the user's responsibility.
- Do not give legal, medical, or financial advice, and do not omit this disclaimer.

---

## 🛠️ Architecture

All skills and rules are stored in tool-agnostic canonical directories:

- **Skills Catalog (English)**: [`skills/en/`](skills/en) (Catalog: [`skills/en/README.md`](skills/en/README.md))
- **Skills Catalog (Japanese)**: [`skills/ja/`](skills/ja) (Catalog: [`skills/ja/README.md`](skills/ja/README.md))
- **Rules**: [`rules/en/`](rules/en) & [`rules/ja/`](rules/ja)
  - **Core Rule**: [`rules/en/fact-grounding-rule.md`](rules/en/fact-grounding-rule.md) (Strict Fact-Grounding & Repository Evidence Rule to eliminate AI hallucinations)
- **Scripts**: [`scripts/`](scripts)

---

## 📋 Installation into Paper Repositories

### Method 1: Git Submodule
```bash
# Replace <your-username> with your actual GitHub username or repository organization
git submodule add https://github.com/<your-username>/scholarly-agent-skills.git .scholarly-agent-skills
python3 .scholarly-agent-skills/scripts/setup_submodule.py --lang en
```

### Method 2: Symlink Installation
```bash
python3 /path/to/scholarly-agent-skills/scripts/link_shared_skills.py /path/to/target-repo --lang en
```

---

## 📂 Artifacts Git Operation & Standard `docs/` Taxonomy

Artifacts in paper repositories are recommended to be organized into the following 5-category structure for maximum readability (when managing multiple papers in a single repo, place this structure under `docs/<paper-id>/`):

- `docs/manuscript/` (or `docs/<paper-id>/manuscript/`): Final paper outputs and rendered formats (`[paper_title].md`, `[paper_title].html`, `[paper_title].pdf`)
- `docs/chapters/`: Chapter drafts and manuscript sections (`chapter1-introduction.md`, `chapter2-macro-and-labor.md`)
- `docs/design/`: Paper outline, test cases, domain concepts, evidence gate reports (`paper-outline.md`, `test-cases.md`, `domain-concepts.md`, `evidence-gate-report.md`)
- `docs/literature/`: Literature matrix, gap reports, glossary, paper reading notes (`literature-matrix.md`, `literature-gap-report.md`, `bilingual-glossary.md`, `papers/*.md`)
- `docs/data/`: Empirical datasets and aggregated statistics (`philippines-poverty-data.md`)

- **Version control is recommended; agent auto-commit is forbidden**: Keep `docs/` reports, inventories, chapter drafts, and manuscripts in Git for traceability. Agents MUST NOT run `git add` / `git commit` after edits. Show changed files and the diff, and commit only when the user explicitly says to commit. Do not treat task completion or a passing quality gate as approval.
- **Commit Forbidden (Must Ignore)**: Raw dataset files (`raw_data/`) and PII mapping files (`mapping.json`) MUST be ignored via `.gitignore` and `python3 scripts/setup_ai_ignore.py` to prevent privacy/security leaks.
