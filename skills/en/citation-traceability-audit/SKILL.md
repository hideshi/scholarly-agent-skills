---
name: citation-traceability-audit
version: 1.3.1
description: Use before submission or after chapter completion to mechanically audit 1-to-1 citation matching and auto-generate references.md
---

# Citation Traceability Audit Skill

## Purpose
Apply static analysis principles to mechanically verify that every citation marker and footnote in manuscript chapters (`docs/chapters/`) matches the Single Source of Truth (`docs/literature/literature-matrix.md`), auto-generating `docs/chapters/references.md` as a derived output.

## Trigger Conditions
- Upon completing each manuscript chapter
- During the automated pre-submission quality gate

## Workflow (4-Step Mechanical Audit & Auto-Generation)

```text
[Step 1: Extract Citations] -> [Step 2: Matrix Cross-Reference] -> [Step 3: Auto-Generate references.md] -> [Step 4: Final 1-to-1 Re-Audit]
```

### Step 1: Extract Manuscript Citation Markers
Run `scripts/check_citation_format.py` to mechanically extract all inline citations (personal surnames `Son, 2010`, institutional acronyms `PSA, 2024`, multi-word names `World Bank, 2026`) and footnotes `[^1]` from `docs/chapters/`:

```bash
python3 scripts/check_citation_format.py docs/chapters/
```

### Step 2: Cross-Reference against Literature Matrix (SoT)
Cross-reference extracted manuscript citations against the Single Source of Truth (`docs/literature/literature-matrix.md`):

```bash
python3 scripts/check_citation_format.py --matrix docs/literature/literature-matrix.md docs/chapters/
```
- **Unregistered Citation Detection**: If a manuscript citation is missing from `literature-matrix.md`, halt generation and return to primary literature ingestion.

### Step 3: Auto-Generate `references.md`
Auto-generate `docs/chapters/references.md` as a derived artifact from `literature-matrix.md`:

```bash
python3 scripts/check_citation_format.py --generate-references docs/chapters/references.md --matrix docs/literature/literature-matrix.md docs/chapters/
```

> ⚠️ **Single Source of Truth (SoT) Rule**: 
> `docs/literature/literature-matrix.md` is the EXCLUSIVE SoT for literature metadata. `docs/chapters/references.md` MUST NOT be manually edited; it must be auto-generated with the `<!-- AUTO-GENERATED -->` header.

### Step 4: Final 1-to-1 Audit
Re-run audit to confirm 0 missing definitions and 0 orphan references.

## Outputs
- Auto-generated `docs/chapters/references.md` (Reference List)
- Audit Log `docs/design/citation-audit.log`
