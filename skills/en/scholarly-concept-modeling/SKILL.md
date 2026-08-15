---
name: scholarly-concept-modeling
version: 1.0.0
description: Use during paper design or novel concept definition to build a domain model dictionary (DDD Ubiquitous Language) and prevent terminological confusion
---

# Scholarly Concept Modeling Skill

## Purpose
Apply Domain-Driven Design (DDD) principles—specifically Ubiquitous Language and Bounded Contexts—to define, structure, and disambiguate core domain concepts (e.g., *agency*, *subjectivity*, *sovereignty*, *inflation*, *consensus*) in paper writing.

## Trigger Conditions
- When creating a thesis outline or chapter structure
- When introducing a new major concept or analytical framework
- When a reviewer notes terminological ambiguity

## Workflow

### Step 1: Create Concept Inventory
Extract core domain terms into `docs/design/domain-concepts.md`:

```markdown
### Concept: [e.g. Agency]
- **Definition in Paper**: The capacity of individual actors to act independently within structural constraints.
- **Bounded Context**: Chapters 2 through 4 (Sociological Analysis).
- **Disambiguation**: Distinct from *Free Will* (philosophical) and *Behavior* (empirical psychology).
- **Contrast with Prior Literature**: Diverges from Smith (2018), who defines agency purely as a structural effect.
```

### Step 2: Automated Term Consistency Check
During drafting and review, the AI Agent verifies that:
1. Defined concepts are not used with meanings that conflict with their definitions.
2. Near-synonyms are not unconsciously substituted for defined terms.

## Outputs
- `docs/design/domain-concepts.md` (Single Source of Truth for Domain Concepts)
