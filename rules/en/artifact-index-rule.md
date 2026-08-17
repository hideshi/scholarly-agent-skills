# Artifact Index & Naming Rule

## Overview
As artifacts accumulate under `docs/<paper-id>/design/` in a paper-writing repository, distinguishing the Source of Truth (SoT) from temporary artifacts comes to depend on human memory, increasing cognitive load. This rule fixes artifacts into six categories and makes "location and structure" mechanically decidable via a four-part set: **category directories, naming patterns, status headers, and INDEX.md**. It reallocates human memory from "content" to "location and structure" (the transactive memory design principle), and assigns rule compliance to the agent, not the human.

---

## 🗂️ 1. Fixed Artifact Categories (6 categories + transcripts)

| Category | Meaning | Naming pattern | Lifecycle |
| :--- | :--- | :--- | :--- |
| **SoT** | Source of Truth. Changes require audit & version control | Header explicitly states "Source of Truth (SoT)" | Permanent, versioned |
| **proposal** | Proposals awaiting adoption | `*-proposal.md` | Adopted → absorbed into SoT or header-promoted (no move/rename); rejected → frozen |
| **brief** | Temporary artifacts for review | `reading-brief-*.md` | Discardable after review; excluded from final/submitted versions |
| **review** | External review records | `*-<model>-review-{brief,result}.md` | Permanent as records |
| **log** | Time-series work records & check results | `*-log.md`, `*-report.md` | Append-only, permanent |
| **notes** | Design exploration memos; not SoT | `*-notes.md` | Role ends once conclusions are reflected in SoT |
| **transcripts** | Session records | `session-transcripts/` | Permanent as records |

> **Invariant 1 (Fixed categories)**: Categories are fixed as above. Do not add new categories (more categories create cognitive load for the index itself). Artifacts that fit no existing category are recorded as `notes` and promoted to SoT when needed.

> **Invariant 2 (Immutability of location)**: Naming patterns and placement directories record the **creation-time** category; the **current category's source of truth is the status header (§3)**. **Never move or rename a file after creation**. On promotion (e.g., proposal → SoT), change only the header; the file keeps its original location and name (to guarantee reference-path stability).

---

## 📁 2. Directory Layout (Standard)

For new repositories and new papers, the standard layout uses category directories:

```text
docs/<paper-id>/design/
├── INDEX.md
├── sot/                    # Source of Truth
├── proposals/              # Proposals
├── briefs/                 # Temporary review artifacts
├── reviews/                # External review records
├── logs/                   # Time-series records & check results
├── notes/                  # Design exploration memos
└── session-transcripts/    # Session records
```

- Naming patterns (§1) are maintained even under directory separation: dual identification preserves decidability when a file is taken out of context.
- Per Invariant 2, mismatches such as an SoT under `proposals/` may arise after promotion; these are accepted as "creation-time category records." Always verify the current category via the header.

### Migration in Existing Repositories (HITL)

- **Initial migration** from a flat layout to category directories requires updating reference paths from other artifacts and the manuscript, and is therefore a **HITL (Human-in-the-Loop) matter**.
- Before migrating, the agent must present the target file list, reference search results, and an update plan, and **may execute only after explicit user approval**. Unapproved automatic migration is prohibited.
- Migration is a one-time event; once completed, Invariant 2 (immutability) applies.

---

## 🏷️ 3. Unified Status Headers

Every artifact states its category in one line at the top, so that opening the file reveals its **current** category without consulting the index.

- **SoT**: `> **Source of Truth (SoT)**: This file is a SoT under design/. See INDEX.md for the artifact category list.`
- **brief**: `> **Temporary review artifact** — exclude from final/submitted versions.`
- **proposal / review / log / notes**: State the category name, creation date, and generating skill in the opening blockquote.
- **On promotion**: Rewrite only the header to the new category (no move/rename; §1 Invariant 2).

---

## 📇 4. Maintaining INDEX.md (Agent Responsibility)

- Maintain a category-organized list (filename + one-line description) in `docs/<paper-id>/design/INDEX.md`.
- **Invariant**: An agent that creates a new artifact **updates INDEX.md within the same session**. Never rely on human memory or manual updates.
- An agent that notices INDEX.md is stale must inventory and update it on the spot ("fix it someday" is prohibited).
- INDEX.md must include the category definition table at the top, so that INDEX.md itself explains the categories (avoid dependence on external documents).

---

## 🚫 5. Prohibitions

- **Do not leave uncategorized artifacts directly under `design/`** (when a new file matches no naming pattern, decide its category and fix its naming/placement at creation time).
- **Never move or rename files after creation** (§1 Invariant 2; initial migration follows the HITL procedure in §2).
- **Never require humans to memorize the rules**. Humans only approve the agent's placement proposals (prevents reproducing the paradox of "demanding organization from those who struggle with it").

---

## Cognitive-Science Basis

Risko & Gilbert (2016) describe the defining attribute of a transactive memory system as "a shift from remembering 'what' to remembering 'where'." This rule makes the "where" mechanically decidable via category directories, naming rules, and INDEX.md, minimizing human-side memory load. Note that the goal is not complete "elimination of memory" but "reallocation of memory" (a coarse-grained memory of the overall structure remains on the human side).
