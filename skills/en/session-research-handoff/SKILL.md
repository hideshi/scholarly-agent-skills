---
name: session-research-handoff
version: 1.0.0
description: Use when ending a session or resuming long-term writing to summarize and restore research context, open questions, and pending tasks
---

# Research Session Handoff Skill

## Purpose
Apply session handoff discipline to preserve research context, active draft state, unverified citations, and pending literature checks across long writing sessions and AI Agent context resets. This ensures smooth continuity for multi-month research projects.

## Trigger Conditions
- At the end of each working session
- When the AI Agent context window limit is approaching
- When transitioning to a different chapter or research sub-topic

## Workflow

### Step 1: Generate Handoff Artifact
At the end of a session, output a structured state summary to `docs/session-handoff.md`:

```markdown
# Research Session Handoff Report

## 1. Current Status
- **Completed Work**: First draft of Chapter 2 "Source A Analysis and Argumentation"
- **Active File**: `manuscript/ch02.md`

## 2. Applied Domain Concepts
- 'Agency' definition: Applied 18th-century Enlightenment model (see `docs/design/domain-concepts.md`)

## 3. Pending Issues
- [ ] Resolve conflict between Smith (2018) and Jones (2021) on the dating of Source B
- [ ] Polish transition language into Chapter 3

## 4. Resume Protocol
1. Load `docs/session-handoff.md`.
2. Resume from Pending Issue #1: Smith/Jones dating conflict.
```

### Step 2: Resume from Handoff
At the start of a new session, the user or AI Agent loads `docs/session-handoff.md` to restore essential research context and active work.

## Outputs
- `docs/session-handoff.md`

