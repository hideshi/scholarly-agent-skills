---
name: submission-venue-advisor
version: 1.0.0
description: Use when a paper draft is complete or when planning preprint publication, to select the optimal submission venue (preprint server or open-access repository) by research field, language, and publication goal
---

# Submission Venue Advisor Skill

## Purpose
When publishing or submitting a completed paper, recommend the optimal preprint server or open-access repository based on research field, manuscript language, and publication goals (establishing priority, gathering pre-review feedback, outreach). Guides the full process from pre-submission quality checks to the submission procedure itself.

## Trigger Conditions
- When a first draft is complete and publication venue is being considered
- When considering preprint publication (priority claim, pre-review feedback)
- When registering a thesis or working paper in a repository

## Venue Classification Matrix

### General-Purpose (All Fields)

| Server | Features | Languages | Cost |
|---|---|---|---|
| **Zenodo** | Operated by CERN. All fields and file formats. Automatic DOI. GitHub integration | Multilingual | Free |
| **OSF (Open Science Framework)** | Project management built in. Strong data/code integration | Multilingual | Free |
| **Research Square** | Interdisciplinary. Optional preprint peer review | Primarily English | Free |

### Field-Specific Preprint Servers

| Field | Recommended Server | Notes |
|---|---|---|
| Economics, Social Sciences, Law | **SSRN** (Elsevier) | Strong working-paper culture; well suited to policy research |
| Physics, Math, CS, Statistics, Econometrics | **arXiv** | Oldest and most influential; includes an econ category |
| Life Sciences | **bioRxiv** | Standard for biology |
| Medicine & Health Sciences | **medRxiv** | Clinical focus; disclaimer required |
| Psychology | **PsyArXiv** | OSF-based |
| Social Sciences (General) | **SocArXiv** | OSF-based; sociology, political science |
| Chemistry | **ChemRxiv** | ACS-affiliated |
| Earth & Environmental Sciences | **EarthArXiv** | Geoscience focus |
| Humanities | **Humanities Commons (CORE)** | MLA-affiliated; accepts short-form works |

### Japanese-Language / Domestic Venues

| Venue | Use Case |
|---|---|
| **J-STAGE** | Electronic platform for Japanese society journals (via society submission) |
| **Zenodo** | Accepts Japanese-language papers; multilingual metadata |
| Institutional repositories | University repositories (e.g., JAIRO Cloud) |

## Selection Criteria

Narrow candidates in this order:

1. **Field convention**: Which server does your field actually read? (Where your reviewers and colleagues look)
2. **Language compatibility**: Non-English manuscripts are safest on Zenodo / OSF / Humanities Commons. SSRN, medRxiv, etc. assume English
3. **DOI assignment**: All major servers above issue DOIs (guarantees citability)
4. **License selection**: CC-BY 4.0 is the standard recommendation; use CC-BY-ND etc. if derivatives should be restricted
5. **Compatibility with future journal submission**: Check the target journal's preprint policy via **SHERPA/RoMEO** (most major publishers permit preprints)

## Pre-Submission Checklist (Quality Gates)

Complete all of the following before submitting:

- [ ] Passed the [`claim-evidence-gate`](../claim-evidence-gate/SKILL.md) quality gate
- [ ] Verified 1-to-1 citation correspondence via [`citation-traceability-audit`](../citation-traceability-audit/SKILL.md)
- [ ] References list fully matches in-text citations
- [ ] Generated the final PDF with `scripts/convert_markdown_to_pdf.py` and visually inspected layout
- [ ] Abstract, keywords, and author information (ORCID recommended) are up to date
- [ ] License (e.g., CC-BY) is stated explicitly
- [ ] Conflict-of-interest and research-ethics statements included (IRB approval number where applicable)

## Multi-Server Deployment (e.g., Zenodo + SSRN)

Registering the same paper on multiple servers is generally acceptable, with these caveats:

- **Version control**: Keep the same version (revision date/number) on every server; update all when revising
- **Cross-linking**: Add the other server's DOI/URL to the related-identifiers field so the records are linked as the same work
- **Distinguish from duplicate submission**: Multiple preprint registrations are fine, but simultaneous submission to peer-reviewed journals violates publication ethics

## Outputs
- `docs/design/submission-plan.md` (Venue selection rationale, submission procedure, publication schedule)
