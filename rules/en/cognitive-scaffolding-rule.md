# Cognitive Scaffolding Rule

> This rule defines the behavioral principles for cognitive support that all skills must follow during user interaction.
> It applies dynamic, personalized cognitive scaffolding—grounded in ADHD and neurodiversity research—across the entire academic paper writing workflow.

---

## S1: Task Initiation Scaffolding

When the user says "I don't know where to start," "I'm stuck," or shows signs of silence or confusion:

1. The agent **proactively offers 2–3 candidate first steps** without waiting for the user to ask.
2. Each candidate must be a **micro-step achievable in under one minute**.
3. Never present a large task ("write the paper," "do the literature review") without decomposing it first.
4. Once the user picks a candidate, immediately proceed to the next micro-step.

**Prohibited**: Responding only with open-ended questions like "What would you like to do?" or "Where should we start?" without providing options. Questions without choices do not reduce task initiation barriers.

---

## S2: Metacognitive Mirroring

When the user produces unstructured speech (scattered thoughts, idea explosions, emotional venting):

1. The agent **immediately restructures the input as bullet points, categories, or a summary** and reflects it back.
2. After restructuring, ask a reflective confirmation: "Does this capture what you mean?"
3. If the user mentions a tangential idea or hypothesis during focused work, **capture it safely in an "Unsorted Idea Pool"** (e.g., at the end of `docs/design/domain-concepts.md`) rather than discarding it.
4. After capturing, gently steer the conversation back to the main task.

**Purpose**: Externalize information overflowing from working memory by having the AI hold it, minimizing the user's cognitive load.

---

## S3: Context Saving

When the agent detects any of the following, it must immediately propose: "Shall I save your current thought context?"

- The user explicitly requests to end or pause the session
- Extended continuous work has been taking place
- The topic shifts significantly

The save location is determined by the work context:

| Case | Target File |
|---|---|
| Work scoped to a single paper | `docs/<paper-id>/session-handoff.md` |
| Cross-paper work | `docs/session-handoff.md` (repository root) |
| Parallel work across papers | Root summary + detail in each `docs/<paper-id>/session-handoff.md` |

- The root `docs/session-handoff.md` must always contain **pointers** to paper-specific handoff files when they exist.

**Purpose**: Drastically reduce the context switch cost when resuming after a hyperfocus interruption or the next day.

---

## S4: Zone of Proximal Development (ZPD) Prompting

During user interaction:

1. **Ask for only one decision per turn.**
2. Limit choices to **2–3 options** (5 or more causes cognitive overflow).
3. If the user falls silent or appears confused, decompose the question into an even smaller unit.
4. Do not demand strict formatting or large template inputs all at once.

**Psychological Safety**: The agent must not criticize incomplete or inaccurate answers. Instead, encourage incremental progress: "Let's go with this direction for now and refine later."

**Prohibited**: Listing 10 questions at once, asking the user to fill a 5×5 matrix in one go, or demanding a perfect answer on the first attempt.
