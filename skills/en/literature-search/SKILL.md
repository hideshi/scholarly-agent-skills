---
name: literature-search
version: 1.0.0
description: Use during research planning or literature search phase to query open-access paper databases (OpenAlex, arXiv, Crossref, Semantic Scholar) and build literature matrices
---

# Multi-Provider Literature Search Skill

## Purpose
Search open-access academic literature across configured providers (OpenAlex, arXiv, Crossref, Semantic Scholar) using [`config/literature_providers.json`](../../../config/literature_providers.json), evaluate relevance, and populate `docs/literature/literature-matrix.md` for downstream gap analysis.

## Trigger Conditions
- At the start of a new research project or thesis chapter
- When a new research question, concept, or claim requires supporting literature
- When a reviewer requests additional references on a specific topic

## Provider Configuration
Add, enable, or disable API endpoints in `config/literature_providers.json`:

```json
{
  "default_provider": "openalex",
  "contact_email": "",
  "providers": {
    "openalex": { "name": "OpenAlex", "type": "openalex_json", "base_url": "https://api.openalex.org/works", "enabled": true },
    "arxiv": { "name": "arXiv", "type": "arxiv_atom", "base_url": "https://export.arxiv.org/api/query", "enabled": true },
    "crossref": { "name": "Crossref", "type": "crossref_json", "base_url": "https://api.crossref.org/works", "enabled": true },
    "semanticscholar": { "name": "Semantic Scholar", "type": "semanticscholar_json", "base_url": "https://api.semanticscholar.org/graph/v1/paper/search", "enabled": true }
  }
}
```

For OpenAlex / Crossref polite-pool access, pass the executor's own contact email via environment variable. Do not commit a personal address. Documentation placeholders such as `example.com` are rejected.

```bash
export SCHOLARLY_CONTACT_EMAIL="firstname.lastname@university.ac.jp"
export SEMANTIC_SCHOLAR_API_KEY="your-key"   # optional; use if you query Semantic Scholar often
```

If the value is unset, empty, or a dummy, the script exits with status 1 without sending HTTP and prints setup steps on stderr. The agent should ask the user for a real address and retry.

## Execution Steps

### Step 1: Run the Search Script
Search across all enabled providers or target a specific one:

```bash
# Search all enabled providers (Submodule: python3 .scholarly-agent-skills/scripts/search_literature.py ...)
python3 scripts/search_literature.py --query "hermeneutics AND 'large language models'" --provider all --max-results 5

# Target a specific provider (e.g., OpenAlex for broad humanities coverage)
python3 scripts/search_literature.py --query "hermeneutics" --provider openalex --max-results 5
```

> [!NOTE]
> When running inside a submodule deployment, prefix script paths with `.scholarly-agent-skills/` (e.g. `python3 .scholarly-agent-skills/scripts/search_literature.py`).

### Step 2: Populate the Literature Matrix
Append high-relevance results to `docs/literature/literature-matrix.md` and pass them to `literature-gap-analysis` (Literature Gap Analysis) for downstream processing.

## Outputs
- Updated `docs/literature/literature-matrix.md`

