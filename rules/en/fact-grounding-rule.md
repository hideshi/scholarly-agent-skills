# Strict Fact-Grounding & Repository Evidence Rule

## Overview
To fundamentally prevent LLM hallucinations (fabrication of numbers, facts, or citations from internal model weights) during academic manuscript writing, this rule mandates **real-time data fetching** and **repository-level data grounding** for all assertions, statistics, and citations.

---

## 🚫 1. Absolute Prohibition of Internal Weight Hallucinations
- AI agents MUST NOT write statistical figures, dates, proper nouns, survey findings, or literature claims into manuscript chapters (`docs/chapters/`) based solely on LLM internal memory/weights.
- Assertions such as "studies show that..." or "approx. XX%" without underlying repository data files are strictly prohibited.

---

## 🌐 2. Two-Phase Information Model (Discovery / Grounding)

All information cited in the manuscript MUST be separated into two phases by purpose.

### 2-A. Discovery — Insufficient as Citation Evidence
- **WebSearch / search snippets / agent internal knowledge**: MAY be used ONLY to identify candidate sources and confirm DOI/arXiv IDs. **MUST NOT** serve as evidence for **content claims about academic literature** (what a study showed or argued).
- **Exception (non-academic sources)**: When an official government or international agency page **is itself primary data** (statistics, policy facts), direct WebFetch of that official page counts as Grounding (equivalent to §2-B).
- **Allowed tools**: `search_literature.py` (candidate identification), WebSearch (bibliographic metadata only)

### 2-B. Grounding — Mandatory for Academic Citations
When citing academic literature in manuscript chapters (`docs/chapters/`), agents MUST create **`docs/<paper-id>/literature/papers/*.md`** via one of:
  1. **PDF ingestion (`convert_pdf_to_markdown.py`)**: Download and convert academic PDFs
  2. **arXiv / open-access full text**: Download and convert to Markdown
  3. **Manual literature stub (`status: manual-stub`)**: For books, theses, or paywalled sources—page-referenced excerpts in frontmatter Markdown (linked to §2 manual primary data inventories)
  4. **Open Data API scripts (`fetch_macro_data.py`, etc.)**: For quantitative claims saved under `docs/data/`

> **Invariant**: `literature-matrix.md` is an index (Discovery artifact) and **MUST NOT** be used as citation evidence. Citation evidence is limited to physical files in `literature/papers/*.md` or `docs/data/`.

---

## 📂 3. Mandatory Repository-Level Data Grounding
- All fetched information MUST be saved as physical data files inside the repository (Git commits are executed upon user approval):
  - **`docs/data/`**: Processed statistical tables, datasets, and indicator files (`*.md`, `*.csv`, `*.json`).
  - **`docs/literature/literature-matrix.md`**: Candidate literature index and gap analysis (**index only—not citation evidence**).
  - **`docs/literature/papers/*.md`**: Primary literature text (ingestion artifacts—**evidence for academic citations**).
- Every statistic or factual claim in `docs/chapters/` MUST link to an existing file in `docs/data/` or `docs/literature/papers/`.

---

## 🔢 4. Quantitative Evidence & Calculation Anchor Rule

When outputting calculated figures (ratios, multipliers, percentage changes, growth rates, disparities, etc.) into manuscript text:

1. **【Mandatory / Text】Immediate Academic Citation Marker**: The paragraph containing the first occurrence of a calculated statistic MUST include a standard academic citation marker (e.g., `(PSA, 2024)` or `[^1]`).
   - ⚠️ **Important (Output Boundary)**: Manuscript text in `docs/chapters/` MUST NOT print local repository file paths (e.g., `data: docs/data/...`) inside citation parentheses. Local file paths are managed exclusively in design and evidence audit documents (`docs/design/`).
2. **【Selective / Recording】Raw Figure / Formula Recording**: The raw values (numerator, denominator, base year) and calculation logic MUST be recorded in at least one of: the manuscript text, a footnote, or a data table in `docs/data/` (e.g., `<!-- tbl-1 -->`).
3. **【Mandatory / Forbidden】Prohibition of Ungrounded Figures**: Outputting ungrounded numerical assertions whose primary source cannot be identified or reproduced from `docs/data/` or primary literature is strictly forbidden.

---

## ⚠️ 5. Enforcement & Build-Blocking Action
- If a statistic, factual claim, or **academic citation** in `docs/chapters/` lacks a corresponding physical evidence file, the AI agent MUST immediately halt writing and:
  1. Execute web search/API tools, PDF ingestion, or manual stub registration to create the required file under `docs/data/` or `docs/literature/papers/`.
  2. Withhold or revise the ungrounded assertion until physical data is secured.
- **Academic citation gate**: When `python3 scripts/check_literature_grounding.py` returns FAIL, block further writing or major edits to the affected chapter/section (WARN allows continued drafting but full-text grounding is recommended before claim-evidence-gate).
- **Gate uses `papers/*.md` as canonical**: PDFs MAY be gitignored; judgments rely on Markdown frontmatter and body text length (reproducible in CI/clean clones).
