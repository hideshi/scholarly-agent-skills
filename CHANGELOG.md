# Changelog

All notable changes to the Scholarly Agent Skills repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.8.0] - 2026-08-20

### Added
- **`reviewer-readability-check` (ja/en) v1.1.0**: section-number integrity checks for the review phase. `check_reviewer_readability.py` now detects branch-suffixed insertion traces (`3.2b`, FAIL), duplicate heading numbers (FAIL), gaps in heading sequences (WARN), and dangling `§x.y` cross-references (WARN; three-level references to external works are out of scope). From jiatama-supremacism friction: a `§3.2b` insertion was discovered by the author, not by any gate.

---

## [1.7.0] - 2026-08-18

### Added
- **`diachronic-claim-typing`** (ja/en) v1.0.0: type diachronic claims (T0–T5, T3b) before literature search and before cross-period sentences; inventory as SoT; prohibition N1 (non-identification). From jiatama-supremacism friction; Kimi K3 APPROVE WITH REVISIONS.

### Changed
- `literature-search` (v1.1.1), `claim-evidence-gate` (v1.4.1), `research-plan-workshop` (v1.0.1): one-line pointers (required).
- `paper-writing-onboarding` (v1.1.1), `literature-gap-analysis` (v1.0.1), `counter-argument-tdd` (v1.4.1): optional pointers.

---

## [1.6.0] - 2026-08-17

### Added
- **Faction & contestation tracking** (ja/en): mechanisms to record and audit scholarly disputes *within* Tier 1 (peer-reviewed) literature, which the Tier system previously treated as flat.
  - `literature-search` (v1.1.0): new Step 1.5 "Faction Discovery" (refutation queries, citation-network scan, retraction/correction checks, camp identification) and extended literature-matrix format with "Position / Camp" and "Contestation Status" columns (`consensus` / `replicated` / `contested` / `contradicted` / `retraction-watch` / `unknown`).
  - `claim-evidence-gate` (v1.4.0): new seventh rubric axis "Field Disagreement" — FAILs claims that assert contested propositions from a single source without acknowledging opposing views, or that cite `contradicted` / `retraction-watch` literature as established knowledge.
  - `counter-argument-tdd` (v1.4.0): new Phase 1 "Faction Check" requiring at least one objection drawn from the opposing camp's representative papers when claims rely on `contested` / `contradicted` literature.
  - `scholarly-concept-modeling` (v1.1.0): new "Contrast with Prior Empirical Claims" field to record proposition-level (not only definitional) disputes.
  - `source-criticism-gate` (v1.1.0): scope note clarifying that Tier judgments cover source types only; within-Tier-1 disputes are delegated to the skills above.

### Changed
- **`pre-reading-briefing` (v1.1.0)** (ja/en): Confirmation questions are typed (`TERM` / `VALID` / `MAP`). The author answers TERM one at a time (cap 3 per session). The agent drafts VALID/MAP with join evidence; the author adopt/rejects 2–3 rows per turn (no accept-all). Ambiguous tags default to TERM. Step 5 no longer asks for every answer.

---

## [1.5.0] - 2026-08-16

### Added
- **`pre-reading-briefing`** (ja/en): Reading-side cognitive scaffolding skill that generates a per-section pre-reading briefing (purpose, prerequisite concepts, main claim, anticipated objection, comprehension check question) before the review/revision phase (PH-REV). Implements the top development priority proposed in the cognitive-scaffolding paper's conclusion (§6.2.3): addressing the production/comprehension asymmetry (§5.1.4) by extending M1 mirroring to the reading side and separating production/comprehension metrics.

---

## [1.4.0] - 2026-08-15

### Added
- **`paper-writing-onboarding`**: Phase-based onboarding from repository setup to first-draft workflow.
- **`research-plan-workshop`**: Interactive one-page research plan (question, audience/venue, definition of done).
- **`submission-venue-advisor`**: Venue selection and submission checklist after quality gates pass.
- **Public-release hygiene**: `CONTRIBUTING.md`, `SECURITY.md`, bilingual `DISCLAIMER.md` (Japanese first, then English), author-responsibility notice in root READMEs and `AGENTS.md`, and configurable polite-pool User-Agent (`SCHOLARLY_CONTACT_EMAIL`, optional `SEMANTIC_SCHOLAR_API_KEY`).
- **Contact-email fail-fast**: `search_literature.py` and `fetch_macro_data.py` refuse to send HTTP when the contact email is unset, empty, or a documentation placeholder (`example.com` etc.), and print agent-actionable setup steps on stderr.

### Changed
- Root `README.md` / `README.en.md` skill lists now match the ja/en catalogs.
- Academic-writing examples no longer use a real author name or an unpublished paper title.
- Source-criticism examples use generic national statistical offices and ministries instead of a single-country case.
- `.gitignore` now excludes `.env`, credentials, and PII mapping files.

---

## [1.3.1] - 2026-08-15

### Added
- **Explicit Citation Output Boundary Rule**: Added strict Output Boundary Rule across `rules/{ja,en}/fact-grounding-rule.md` and `skills/{ja,en}/claim-evidence-gate/SKILL.md` forbidding local repository file paths (`data: docs/data/...`) from being printed inside manuscript text (`docs/chapters/`) citation parentheses.
- **Clean Academic Citation Standard**: Enforced pure APA/Harvard academic citations (e.g. `(PSA, 2024)`, `(World Bank, 2026)`) for published manuscript prose, reserving local table paths exclusively for `docs/data/` table notes and `docs/design/` audit reports.

---

## [1.3.0] - 2026-08-15

### Added
- **4-Layer Architecture & Single Source of Truth (SoT)**: Established clear separation between Rule Layer (`rules/`), Skill Layer (`skills/`), Script Layer (`scripts/`), and Data Layer (`docs/data/`).
- **Quantitative Evidence & Calculation Anchor Rule**: Authored SoT rule in `rules/{ja,en}/fact-grounding-rule.md` requiring paragraph-level primary citation markers, raw figure/formula recording in text/footnotes/`docs/data/`, and prohibiting ungrounded numerical assertions.
- **Externalized Pattern Configuration**: Created `config/numeric_patterns.json` for project-specific unit and currency term customization.
- **Candidate Extractor Linter**: Refactored `scripts/check_fact_grounding.py` into a coarse recall-focused candidate extractor with false-positive exclusions for years (`1999`, `2024`), section numbers (`3.1`), page numbers (`p.45`), code blocks, and support for Harvard citations `(Author, YYYY)`.
- **Data Table ID Conventions**: Standardized HTML comment IDs (`<!-- tbl-1 -->`) and formula notes in `docs/data/` for unambiguous cross-referencing.
- **Generalized Data Re-Interpretation Check**: Added 3-axis numerical counter-argument evaluation (Pace/Elasticity, Absolute Benchmark, Factor Decomposition) to `counter-argument-tdd`.

### Changed
- **`claim-evidence-gate` (v1.2.0 -> v1.3.0)**: Integrated quantitative anchor criteria into `Direct Match` axis (maintaining 6-axis rubric simplicity) and added `check_fact_grounding.py` pre-filter step in Step 1.
- **`counter-argument-tdd` (v1.2.0 -> v1.3.0)**: Updated Japanese and English skill files with generalized 3-axis numerical counter-argument evaluation.
- **`tests/test_check_fact_grounding.py`**: Added comprehensive regression test suite (51 total unit tests passing).

---

## [1.2.0] - 2026-08-15

### Added
- **6-Axis Rubric Expansion**: Separated `Modality Alignment` into `Modality Alignment` (tone vs evidence scale) and `Benchmark Grounding` (explicit baseline/threshold at first occurrence).
- **`N/A` (Not Applicable) Rules**: Explicit N/A handling for non-group claims (`Internal Heterogeneity`) and non-comparative claims (`Benchmark Grounding`).
- **Output Boundary Enforcement Linter**: Added `scripts/check_output_boundary.py` and unit tests in `tests/test_check_output_boundary.py`.
- **Mandatory Heterogeneity Logging**: Required explicit logging of heterogeneity counter-arguments or N/A justifications in `docs/design/test-cases.md`.

---

## [1.1.0] - 2026-08-15

### Added
- Added `Internal Heterogeneity` evaluation axis to `claim-evidence-gate`.
- Added `Heterogeneity Check` to `counter-argument-tdd`.
- Added `Output Boundary Rule` separating internal workflow labels from published manuscript prose.

---

## [1.0.0] - 2026-08-15

### Added
- Initial canonical release of scholarly agent skills and rules framework (Japanese `ja/` & English `en/`).
