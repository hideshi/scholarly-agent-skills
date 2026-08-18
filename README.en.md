# Scholarly Agent Skills (Thesis-Driven Development)

> **AI Agent skills & rules for Academic Research, Literature Search, and Paper Writing across all disciplines.**  
> Software engineering discipline (DDD, TDD, Spec Gap Analysis, Invariant Validation, Handoff) applied to academic research, literature review, and paper writing. Multi-platform support for Cursor, Claude Code, OpenAI Codex, Antigravity, etc.

---

## 💡 Concept

This repository provides **tool-agnostic AI agent skills and rules** that function seamlessly across any AI coding/agent environment. It supports academic paper writing across all disciplines—including Humanities, Social Sciences, Natural Sciences, Engineering, and Medicine.

**論文の内容・出典・投稿に関する最終責任は、常に著者（利用者）にあります。** Authors remain responsible for the manuscript, citations, and any submission. See [DISCLAIMER.md](DISCLAIMER.md) and the “免責事項 / Disclaimer” section below. The Japanese text comes first.

- **`paper-writing-onboarding`**: Guide first-time paper writers through setup and the phase-based writing workflow.
- **`research-plan-workshop`**: Lock the research question, audience/venue, and definition of done into a one-page plan through dialogue.
- **`primary-data-integration`**: Structure, catalog, and integrate primary empirical data into thesis claims and evidence statements.
- **`scholarly-concept-modeling`**: Domain-Driven Design (DDD) principles applied to define polysemic and domain concepts with bounded contexts.
- **`counter-argument-tdd`**: Test-Driven Development (TDD) principles applied to draft counter-arguments (Red) before writing main paragraphs (Green/Refactor).
- **`claim-evidence-gate`**: Invariant validation discipline to audit claims against primary sources, empirical data, and citations.
- **`literature-gap-analysis`**: Spec Gap Analysis to compare existing literature (AS-IS) with paper novelty (TO-BE) for Introduction sections.
- **`literature-search`**: Multi-provider open-access paper search across OpenAlex, arXiv, Crossref, and Semantic Scholar.
- **`diachronic-claim-typing`**: Type diachronic claims and audit period-section selection, transmission, continuity, and novelty over-claims.
- **`source-criticism-gate`**: Audit source trustworthiness (Tier 1–3) and block unverified websites, blogs, or social media.
- **`pdf-paper-ingestion`**: Native PDF paper conversion to Markdown with automatic figure/image extraction.
- **`academic-paper-translation`**: Translate foreign papers into configured native language with bilingual glossaries and parallel paragraphs.
- **`citation-traceability-audit`**: Audit 1-to-1 matching between body text claims, footnotes, and bibliography references.
- **`session-research-handoff`**: Maintain research context and unverified claims across long writing sessions.
- **`pre-reading-briefing`**: Present per-section prerequisites, claims, and anticipated objections before draft read-through, lowering review-phase comprehension cost.
- **`submission-venue-advisor`**: Recommend a submission venue (preprint server / repository) by field, language, and publication goal.

See the full catalogs in [`skills/ja/README.md`](skills/ja/README.md) and [`skills/en/README.md`](skills/en/README.md).

---

## 🛠️ Installation Guide for Paper Repositories

There are **two ways** to install these skills into your paper repository (both use Python 3 standard library):

### Method 1: Git Submodule (Recommended for Collaboration & Portability)
```bash
git submodule add https://github.com/<your-username>/scholarly-agent-skills.git .scholarly-agent-skills
python3 .scholarly-agent-skills/scripts/setup_submodule.py --lang en
```

### Method 2: Symlink Installation (Ideal for Local Multi-Project Management)
```bash
python3 /path/to/scholarly-agent-skills/scripts/link_shared_skills.py /path/to/your-paper-repo --lang en
```

---

## 🔌 External API Contact and Keys

Literature search and macro-data scripts call public APIs. OpenAlex and Crossref recommend a **contact email in the User-Agent** for their polite pools. Do not commit a personal email to git.

```bash
# Required: the executor's own address (documentation placeholders such as example.com are rejected)
export SCHOLARLY_CONTACT_EMAIL="firstname.lastname@university.ac.jp"

# Optional, if you query Semantic Scholar often
export SEMANTIC_SCHOLAR_API_KEY="your-key"
```

You can also set `contact_email` in [`config/literature_providers.json`](config/literature_providers.json). The environment variable wins when both are set. If the value is unset, empty, or a dummy such as `you@example.com`, the scripts **exit with status 1 without sending HTTP** and print setup steps on stderr for the agent.

---

## 🌐 i18n (Japanese / English)

- **Japanese skills (`skills/ja/`)**: Academic plain style (である調) and Japanese scholarly conventions.
- **English skills (`skills/en/`)**: Topic-sentence-first, active voice, and signposting conventions.

---

## 免責事項 / Disclaimer

The canonical full text is [DISCLAIMER.md](DISCLAIMER.md) (Japanese first, then English).

本リポジトリは学術研究と論文執筆を支援する無保証のツールであり、法律・医療・投資その他の専門助言ではありません。生成文の正確性、出典の真正性、投稿規定への適合、研究倫理・個人情報の適法性は保証しません。品質ゲートを通しても誤りは残り得ます。外部APIの利用規約と User-Agent の連絡先は実行者の責任です。著作物は利用権がある場合に限り取り込んでください。ソフトウェアは MIT License のもと現状有姿で提供されます。

This repository is an as-is research-writing aid, not professional advice. Authors remain responsible for claims, citations, ethics, and submissions. Quality gates can miss errors. Venue guidance is not a guarantee. API terms and the User-Agent contact email are the executor's responsibility. Ingest copyrighted works only with a right to do so. The software is provided under the MIT License, as is, without warranty.

---

## 📜 License

MIT License. See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines, [SECURITY.md](SECURITY.md) to report vulnerabilities, and [DISCLAIMER.md](DISCLAIMER.md) for the full disclaimer.
