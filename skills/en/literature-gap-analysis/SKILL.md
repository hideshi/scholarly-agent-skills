---
name: literature-gap-analysis
version: 1.0.1
description: Use during literature review or introduction drafting to extract gaps between current literature (AS-IS) and proposed contribution (TO-BE)
---

# Literature Gap Analysis Skill

## Purpose
Apply Spec Gap Analysis discipline to compare existing literature (AS-IS) with the proposed paper's novelty (TO-BE), clearly defining the research gap and contribution for Introduction and Related Work sections.

## Trigger Conditions
- When drafting the Introduction or Related Work section
- When defining the paper's novel contribution after completing the literature review
- When a reviewer questions the paper's originality

## Workflow

### Step 1: Summarize Prior Art (AS-IS)
Extract key findings, methods, and datasets from `docs/literature/literature-matrix.md` to establish the current state of knowledge.

### Step 2: Construct the Gap Matrix (TO-BE vs AS-IS)
Create a structured comparison matrix highlighting the specific gaps this paper fills:

```markdown
| Research Dimension | Existing Literature (AS-IS) | Proposed Paper (TO-BE) | Novel Contribution (Gap) |
|---|---|---|---|
| Dataset / Sources | Public macro statistics | Micro-level archival records | Data granularity expansion |
| Methodology | Qualitative case study | Mixed-methods NLP analysis | Methodological framework renewal |
| Scope / Conclusion | Domain-specific validity only | Cross-domain applicability demonstrated | Scope extension & theoretical revision |
```

### Step 3: Generate Contribution Statement
Based on the extracted gaps, compose a positioning statement for the Introduction: "While prior work has focused on X using method Y, this paper employs Z to reveal W, thereby addressing the gap of..." If the novelty is a genealogical connection and T3 in [`diachronic-claim-typing`](../diachronic-claim-typing/SKILL.md) has not passed, downgrade it to juxtaposition/comparison.

## Outputs
- `docs/literature/literature-gap-report.md` (Literature Gap Report)

