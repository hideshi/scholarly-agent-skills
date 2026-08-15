# Strict Fact-Grounding & Repository Evidence Rule

## Overview
To fundamentally prevent LLM hallucinations (fabrication of numbers, facts, or citations from internal model weights) during academic manuscript writing, this rule mandates **real-time data fetching** and **repository-level data grounding** for all assertions, statistics, and citations.

---

## 🚫 1. Absolute Prohibition of Internal Weight Hallucinations
- AI agents MUST NOT write statistical figures, dates, proper nouns, survey findings, or literature claims into manuscript chapters (`docs/chapters/`) based solely on LLM internal memory/weights.
- Assertions such as "studies show that..." or "approx. XX%" without underlying repository data files are strictly prohibited.

---

## 🌐 2. Mandatory Primary Data & Internet Fetching
- All information cited or referenced in the manuscript MUST be fetched live through:
  1. **Web Search & URL Fetching Tools**: Real-time searching and reading of official websites and published reports.
  2. **Open Data API Scripts (`fetch_macro_data.py`)**: Live data fetching from official APIs (e.g., World Bank Open Data API).
  3. **PDF Ingestion Tools (`convert_pdf_to_markdown.py`)**: Conversion and parsing of downloaded academic PDFs.
  4. **Manual Primary Data Inventories**: Verified datasets collected offline or via subscription databases (e.g., JSTOR).

---

## 📂 3. Mandatory Repository-Level Data Grounding
- All fetched information MUST be saved as physical data files inside the repository (Git commits are executed upon user approval):
  - **`docs/data/`**: Processed statistical tables, datasets, and indicator files (`*.md`, `*.csv`, `*.json`).
  - **`docs/literature/`**: Literature matrices, gap reports, and paper notes (`*.md`).
- Every statistic or factual claim in `docs/chapters/` MUST link to an existing file in `docs/data/` or `docs/literature/`.

---

## 🔢 4. Quantitative Evidence & Calculation Anchor Rule

When outputting calculated figures (ratios, multipliers, percentage changes, growth rates, disparities, etc.) into manuscript text:

1. **【Mandatory / Text】Immediate Academic Citation Marker**: The paragraph containing the first occurrence of a calculated statistic MUST include a standard academic citation marker (e.g., `(PSA, 2024)` or `[^1]`).
   - ⚠️ **Important (Output Boundary)**: Manuscript text in `docs/chapters/` MUST NOT print local repository file paths (e.g., `data: docs/data/...`) inside citation parentheses. Local file paths are managed exclusively in design and evidence audit documents (`docs/design/`).
2. **【Selective / Recording】Raw Figure / Formula Recording**: The raw values (numerator, denominator, base year) and calculation logic MUST be recorded in at least one of: the manuscript text, a footnote, or a data table in `docs/data/` (e.g., `<!-- tbl-1 -->`).
3. **【Mandatory / Forbidden】Prohibition of Ungrounded Figures**: Outputting ungrounded numerical assertions whose primary source cannot be identified or reproduced from `docs/data/` or primary literature is strictly forbidden.

---

## ⚠️ 5. Enforcement & Build-Blocking Action
- If a statistic or factual claim in `docs/chapters/` lacks a corresponding physical evidence file in `docs/data/` or `docs/literature/`, the AI agent MUST immediately halt writing and:
  1. Execute web search/API tools or primary data logging to create the required file under `docs/data/` or `docs/literature/`.
  2. Withhold or revise the ungrounded assertion until physical data is secured.
