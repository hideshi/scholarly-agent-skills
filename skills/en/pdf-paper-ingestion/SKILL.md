---
name: pdf-paper-ingestion
version: 1.4.0
description: Use when ingesting downloaded PDF papers to extract text outline structure and extract embedded images (JPEG/PNG) into Markdown (Note: scanned image PDFs require external OCR)
---

# PDF Paper Ingestion Skill

## Purpose
Convert digital PDF paper files into structured Markdown while natively extracting embedded figures, diagrams, and images into `assets/` directories. Uses only Python standard library—no third-party dependencies required.

## Trigger Conditions
- When a PDF paper has been downloaded from a digital library, arXiv, or journal website
- When a PDF paper needs to be structured for text analysis or downstream skills

> [!WARNING]
> **Known Limitations**:
> 1. **Scanned PDFs (image-only)**: No embedded text → empty body; OCR required.
> 2. **CJK CIDFont PDFs**: Garbled or empty text extraction.
> 3. **Encrypted / password-protected PDFs**: Rejected with an error.
> 4. **Publisher bot challenges (reCAPTCHA / Cloudflare Turnstile, etc.)**: `download_literature_pdf.py` **stops immediately and hands off to the user** when it detects a challenge page (Step 1b). Do not attempt browser automation to bypass.
> 5. **Publisher paywalls (Wiley, MISQ, etc., without bot interstitial)**: May fail with HTTP 403 → human handoff or `manual-stub` with page-verified excerpts.
> 6. **Books & theses**: No automatic download → `manual-stub` with page excerpts.
> 7. **Institutional repositories** (Bristol, UvA Pure, etc.): Non-standard URLs often missing from APIs → fallback URL list is a future extension.

> Full backlog: [`docs/design/literature-download-backlog.md`](../../../docs/design/literature-download-backlog.md)

## Execution Steps

### Step 1: Fetch OA PDF (when DOI is known)

Resolve and download open-access PDFs via OpenAlex / Semantic Scholar:

```bash
export SCHOLARLY_CONTACT_EMAIL="firstname.lastname@university.ac.jp"

python3 scripts/download_literature_pdf.py \
  --doi 10.1007/s00146-010-0272-8 \
  --slug kirsh-2010 \
  --output-dir docs/literature/papers/_downloads/

# Batch: all frontmatter status=abstract-only under papers/
python3 scripts/download_literature_pdf.py \
  --papers-dir docs/literature/papers/ \
  --status-filter abstract-only \
  --output-dir docs/literature/papers/_downloads/ \
  --ingest
```

> Paywalled publishers (Wiley, MISQ, etc.) may still fail — log in `_ingestion-log.md` and use `manual-stub` with page-verified excerpts. **When the script reports `bot-challenge (reCAPTCHA/Cloudflare): human handoff required`, go to Step 1b (no retry loops on the same URL).**

**`_downloads/` as primary source**: keep fetched PDFs at `docs/<paper-id>/literature/papers/_downloads/{slug}.pdf` and **do not gitignore them** (they are the re-auditable original). The Markdown note is a transcription; `status: full-text` without a matching PDF is a grounding WARN. Do not download PDFs the user has no right to redistribute.

### Step 1b: Human PDF handoff (bot challenge detected)

When `download_literature_pdf.py` returns `bot-challenge (reCAPTCHA/Cloudflare): human handoff required`, **stop automated fetch and ask the user**. Do not retry with browser MCP, curl loops, or unofficial mirrors.

**User request template**:

1. Open `source_url` from `papers/{slug}.md` (or the DOI landing page) in a browser
2. Complete reCAPTCHA / Cloudflare and download the official PDF
3. Save to `docs/<paper-id>/literature/papers/_downloads/{slug}.pdf` (**rename to slug** if the publisher uses a long filename)
4. Ask the agent to re-run `check_literature_grounding.py` (and `convert_pdf_to_markdown.py` if upgrading to `full-text`)

**Example**: Wood et al. (1976) — Free Access on Wiley/ACAMH but blocked by Cloudflare for automation (2026-08-20). Resolved when the user placed `_downloads/wood-1976.pdf`.

### Step 2: Run the PDF Conversion Script
Execute the included [`scripts/convert_pdf_to_markdown.py`](../../../scripts/convert_pdf_to_markdown.py):

```bash
# Basic usage (Submodule: python3 .scholarly-agent-skills/scripts/convert_pdf_to_markdown.py ...)
python3 scripts/convert_pdf_to_markdown.py path/to/paper.pdf

# Specify an output directory
python3 scripts/convert_pdf_to_markdown.py path/to/paper.pdf --output-dir docs/literature/papers/
```

> [!NOTE]
> When running inside a submodule deployment, prefix script paths with `.scholarly-agent-skills/` (e.g. `python3 .scholarly-agent-skills/scripts/convert_pdf_to_markdown.py`).

### Step 3: Output Verification & Fallbacks

- **Normal Success**:
  - `[paper_name].md`: Extracted section headings, text body, and image links.
  - `assets/` directory: Extracted figure files.
- **PPM → PNG auto-normalization (v1.1.0)**:
  - FlateDecode images are first saved as `.ppm` (stdlib-only extraction).
  - When **Pillow** or **ImageMagick** (`convert` / `magick`) is available, they are converted to `.png` immediately and Markdown links use `.png`.
  - To normalize existing `.ppm` files only:
    ```bash
    python3 scripts/convert_pdf_to_markdown.py \
      --normalize-ppm-dir docs/literature/papers/assets \
      --update-md docs/literature/papers/risko-gilbert-2016.md
    ```
- **Fallbacks (Scanned, CJK CIDFont, or Encrypted PDFs)**:
  If the standard script cannot decode text accurately, recommend or use third-party libraries:
  - **pymupdf (`fitz`) / pdfplumber**: High-accuracy text and CJK encoding extraction
  - **tesseract OCR / ocrmypdf**: Automatic text extraction from scanned PDFs

### Step 4: Feed into Downstream Analysis
Pass the converted Markdown file to `literature-gap-analysis` (Literature Gap Analysis) or `claim-evidence-gate` (Evidence Gate) for detailed textual critique.

## Outputs
- `docs/literature/papers/_downloads/[paper_name].pdf` (primary source; version-controlled)
- `docs/literature/papers/[paper_name].md`
- `docs/literature/papers/assets/extracted_image_*.jpg`
- `docs/literature/papers/assets/extracted_image_*.png` (when PPM normalization succeeds)

