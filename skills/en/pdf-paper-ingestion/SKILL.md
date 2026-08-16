---
name: pdf-paper-ingestion
version: 1.1.0
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
> 1. **Scanned PDFs (Image-Only)**: PDFs lacking text streams yield empty text body. External OCR is required.
> 2. **CJK (Chinese/Japanese/Korean) CIDFont PDFs**: May yield garbled or empty text due to custom font encodings.
> 3. **Encrypted / Password-Protected PDFs**: Rejected with an error.

## Execution Steps

### Step 1: Run the PDF Conversion Script
Execute the included [`scripts/convert_pdf_to_markdown.py`](../../../scripts/convert_pdf_to_markdown.py):

```bash
# Basic usage (Submodule: python3 .scholarly-agent-skills/scripts/convert_pdf_to_markdown.py ...)
python3 scripts/convert_pdf_to_markdown.py path/to/paper.pdf

# Specify an output directory
python3 scripts/convert_pdf_to_markdown.py path/to/paper.pdf --output-dir docs/literature/papers/
```

> [!NOTE]
> When running inside a submodule deployment, prefix script paths with `.scholarly-agent-skills/` (e.g. `python3 .scholarly-agent-skills/scripts/convert_pdf_to_markdown.py`).

### Step 2: Output Verification & Fallbacks

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

### Step 3: Feed into Downstream Analysis
Pass the converted Markdown file to `literature-gap-analysis` (Literature Gap Analysis) or `claim-evidence-gate` (Evidence Gate) for detailed textual critique.

## Outputs
- `docs/literature/papers/[paper_name].md`
- `docs/literature/papers/assets/extracted_image_*.jpg`
- `docs/literature/papers/assets/extracted_image_*.png` (when PPM normalization succeeds)

