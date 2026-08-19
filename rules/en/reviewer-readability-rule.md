# Reviewer-Readability Rule

## Overview
Manuscript chapters (`docs/<paper-id>/chapters/`) are the reviewer-facing academic layer. To prevent internal symbols and workflow jargon from leaking into prose, mechanical checking with `scripts/check_reviewer_readability.py` is **mandatory when a chapter is written or revised** and **when the manuscript is assembled**.

---

## 📚 1. Three-Layer Vocabulary Separation

| Layer | Scope | Rule |
| :--- | :--- | :--- |
| **Prose** | Paragraphs, headings, lists in chapter files | Academic description only. Internal codes (`PROP-*`, `SCAF-FAIL`, `RQ-*`, `PH-*`), JST timestamps, and version numbers are removed by default. Section numbers must be a plain sequence: no branch suffixes (`3.2b`), gaps, duplicates, or dangling `§` references |
| **Tables** | Markdown tables (lines starting with `\|`) | Codes may remain, but an accompanying gloss (table note or in-cell) is required |
| **Appendix / SoT** | Appendices A–C, verification inventory, dialogue logs | Full code definitions and audit trail. Exempt from scanning |

## ✍️ 2. Negative-case IDs in prose (prose-gloss)
- Refer to negative cases as "a case of X was observed (NC-05)"; never make the ID the sentence subject
- Adjacent gloss form "NC-01 (figure rejection)" is also acceptable

## 🚦 3. Mandatory Trigger Points

1. **Chapter completion**: after writing or revising a chapter file, run
   ```bash
   python3 scripts/check_reviewer_readability.py docs/<paper-id>/chapters/<file>.md
   ```
2. **Manuscript build**: `assemble_manuscript.py` runs the check automatically and aborts on FAIL (bypass only with `--force`, recording the reason in the decision log)
3. **Pre-submission**: executed as check #5 of `check_pre_submission.py`

## ⚠️ 4. Handling Findings
- **FAIL**: always fix. Classification as "acceptable" is not allowed (follow the pattern table in the `reviewer-readability-check` skill, Step 2)
- **WARN**: triage via the `reviewer-readability-check` skill; "acceptable" decisions require author approval and logging
- **Deliberate exceptions**: add `<!-- readability:ignore -->` to the line and record the rationale in `docs/<paper-id>/design/logs/reviewer-readability-log.md`

## 📖 5. Where Codes Are Defined
- Reader-facing excerpt: the paper's Appendix A.3 (glossary)
- Full system of record: verification inventory §4.2 (codebook)
