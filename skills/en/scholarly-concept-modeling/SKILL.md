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

### Step 1.5: Idea Explosion Capture
If the user mentions tangential ideas, hypotheses, or inspirations during concept definition dialogue, the agent must not discard them. Instead, append them to the end of `docs/<paper-id>/design/domain-concepts.md` (or `docs/design/domain-concepts.md`) in the following format:

```markdown
## Unsorted Idea Pool
- [timestamp] Summary of user's remark (emerged during definition of Concept X)
- [timestamp] ...
```

This safely captures ideas overflowing from working memory without disrupting the main task (concept definition). Implements [Cognitive Scaffolding Rule S2](../../../rules/en/cognitive-scaffolding-rule.md).

### Step 2: Automated Term Consistency Check
During drafting and review, the AI Agent verifies `docs/<paper-id>/design/domain-concepts.md` (or `docs/design/domain-concepts.md`) to check that:
1. Defined concepts are not used with meanings that conflict with their definitions.
2. Near-synonyms are not unconsciously substituted for defined terms.
3. The agent reflects the user's recent statements back ("You're using this term to mean X, correct?") and checks for discrepancies with the definition (S2: Metacognitive Mirroring).

## Cognitive Scaffolding
All interactions in this skill must follow the [Cognitive Scaffolding Rule](../../../rules/en/cognitive-scaffolding-rule.md) (S1–S4). Concept definition dialogues are particularly prone to thought divergence, so S2 (Metacognitive Mirroring) takes priority.

## Outputs
- `docs/design/domain-concepts.md` (Single Source of Truth for Domain Concepts)
