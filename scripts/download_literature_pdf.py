#!/usr/bin/env python3
"""
Resolve and download open-access PDFs for literature grounding.

Resolves candidate PDF URLs via OpenAlex and Semantic Scholar, downloads with
publisher-appropriate headers (Referer for Springer/Wiley), validates PDF magic
bytes, detects bot-challenge HTML (reCAPTCHA / Cloudflare) for human handoff,
and optionally hands off to convert_pdf_to_markdown.py.

Uses ONLY Python standard library.

Future work / known gaps: docs/design/literature-download-backlog.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from contact_email import ContactEmailError, require_contact_email
from search_literature import build_request_headers, load_config

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
PDF_MAGIC = b"%PDF"
MIN_PDF_BYTES = 1024

# HTML bot-challenge pages (reCAPTCHA, Cloudflare Turnstile, etc.) cannot be solved by scripts.
BOT_CHALLENGE_MARKERS = (
    b"recaptcha",
    b"g-recaptcha",
    b"cf-turnstile",
    b"challenges.cloudflare.com",
    b"just a moment",
    b"performing security verification",
    b"checking your browser",
    b"bot detection",
    b"turnstile",
)

HUMAN_PDF_HANDOFF_TEMPLATE = """\
HUMAN HANDOFF (bot challenge): Automated download cannot pass reCAPTCHA / Cloudflare Turnstile.

Ask the user to:
1. Open the official landing page in a browser: {landing}
2. Complete the challenge and download the PDF.
3. Save as: docs/<paper-id>/literature/papers/_downloads/{slug}.pdf
4. Re-run check_literature_grounding.py (and convert_pdf_to_markdown.py if upgrading to full-text).

Do NOT retry the same URL in a loop or use unauthorized mirrors.
"""


def is_bot_challenge_html(data: bytes) -> bool:
    """Return True when response body looks like a CAPTCHA / bot-check interstitial."""
    if not data or data.startswith(PDF_MAGIC):
        return False
    head = data[:8192].lower()
    if b"<html" not in head and b"<!doctype html" not in head:
        return False
    return any(marker in head for marker in BOT_CHALLENGE_MARKERS)


def format_human_handoff(slug: str, landing_url: str = "") -> str:
    landing = landing_url.strip() or f"(see source_url in literature/papers/{slug}.md)"
    return HUMAN_PDF_HANDOFF_TEMPLATE.format(slug=slug, landing=landing)


def needs_human_handoff(error_message: str) -> bool:
    lowered = (error_message or "").lower()
    return "bot-challenge" in lowered or "human handoff" in lowered


@dataclass
class DownloadResult:
    doi: str
    slug: str
    success: bool
    pdf_path: Optional[Path]
    source: str
    message: str


def parse_frontmatter(text: str) -> Dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    meta: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def normalize_doi(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    return value


def infer_referer(pdf_url: str) -> Optional[str]:
    """Publisher CDNs often require a Referer matching the article landing page."""
    parsed = urllib.parse.urlparse(pdf_url)
    host = parsed.netloc.lower()
    path = parsed.path

    springer_match = re.search(r"/content/pdf/(10\.\d+/[^/?#]+)", path, re.I)
    if "springer.com" in host and springer_match:
        doi = springer_match.group(1).removesuffix(".pdf")
        return f"https://link.springer.com/article/{doi}"

    wiley_match = re.search(r"/doi/pdfdirect/(10\.\d+/[^/?#]+)", path, re.I)
    if "wiley.com" in host and wiley_match:
        doi = wiley_match.group(1)
        return f"https://onlinelibrary.wiley.com/doi/{doi}"

    wiley_pdf_match = re.search(r"/doi/pdf/(10\.\d+/[^/?#]+)", path, re.I)
    if "wiley.com" in host and wiley_pdf_match:
        doi = wiley_pdf_match.group(1)
        return f"https://onlinelibrary.wiley.com/doi/{doi}"

    return None


def fetch_json(url: str, headers: dict, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def resolve_pdf_candidates(doi: str, headers: dict) -> List[Tuple[str, str]]:
    """Return ordered (source_label, pdf_url) candidates for a DOI."""
    doi = normalize_doi(doi)
    if not doi:
        return []

    candidates: List[Tuple[str, str]] = []
    seen: set[str] = set()

    def add(label: str, url: Optional[str]) -> None:
        if not url:
            return
        url = url.strip()
        if not url.startswith("http"):
            return
        key = url.rstrip("/").lower()
        if key in seen:
            return
        seen.add(key)
        candidates.append((label, url))

    # OpenAlex
    try:
        oa_url = f"https://api.openalex.org/works/https://doi.org/{urllib.parse.quote(doi)}"
        work = fetch_json(oa_url, headers)
        best = work.get("best_oa_location") or {}
        add("openalex:best", best.get("pdf_url"))
        for idx, loc in enumerate(work.get("locations") or []):
            add(f"openalex:loc{idx}", loc.get("pdf_url"))
    except Exception as exc:
        print(f"⚠️  OpenAlex lookup failed for {doi}: {exc}", file=sys.stderr)

    # Semantic Scholar (rate-limit sensitive — single call)
    try:
        s2_url = (
            "https://api.semanticscholar.org/graph/v1/paper/"
            f"DOI:{urllib.parse.quote(doi)}?fields=openAccessPdf"
        )
        s2_headers = dict(headers)
        api_key = __import__("os").environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
        if api_key:
            s2_headers["x-api-key"] = api_key
        paper = fetch_json(s2_url, s2_headers)
        oap = paper.get("openAccessPdf") or {}
        add("semanticscholar", oap.get("url"))
    except Exception as exc:
        print(f"⚠️  Semantic Scholar lookup failed for {doi}: {exc}", file=sys.stderr)

    return candidates


def is_valid_pdf_bytes(data: bytes) -> bool:
    if len(data) < MIN_PDF_BYTES:
        return False
    if not data.startswith(PDF_MAGIC):
        return False
    # Reject HTML error pages mislabeled as downloads
    head = data[:256].lower()
    if b"<html" in head or b"<!doctype html" in head:
        return False
    return True


def download_pdf_url(
    url: str,
    dest: Path,
    headers: dict,
    referer: Optional[str] = None,
    timeout: int = 60,
) -> Tuple[bool, str]:
    req_headers = dict(headers)
    req_headers.setdefault("Accept", "application/pdf,application/octet-stream,*/*")
    if referer:
        req_headers["Referer"] = referer
    elif infer_referer(url):
        req_headers["Referer"] = infer_referer(url)

    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        body = b""
        try:
            body = exc.read()
        except Exception:
            pass
        if is_bot_challenge_html(body) or exc.code in (403, 429, 503):
            return False, "bot-challenge (reCAPTCHA/Cloudflare): human handoff required"
        return False, f"HTTP {exc.code}"
    except Exception as exc:
        return False, str(exc)

    if not is_valid_pdf_bytes(data):
        if is_bot_challenge_html(data):
            return False, "bot-challenge (reCAPTCHA/Cloudflare): human handoff required"
        return False, "not a valid PDF (empty, HTML, or too small)"

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return True, f"{len(data)} bytes"


def download_for_doi(
    doi: str,
    slug: str,
    output_dir: Path,
    headers: dict,
    dry_run: bool = False,
) -> DownloadResult:
    doi = normalize_doi(doi)
    dest = output_dir / f"{slug}.pdf"
    candidates = resolve_pdf_candidates(doi, headers)

    if not candidates:
        return DownloadResult(doi, slug, False, None, "", "no OA PDF URL found")

    if dry_run:
        lines = "; ".join(f"{label}={url}" for label, url in candidates[:5])
        return DownloadResult(doi, slug, True, dest, "dry-run", lines)

    last_error = "unknown"
    for label, url in candidates:
        print(f"   ↳ trying {label}: {url}", file=sys.stderr)
        ok, msg = download_pdf_url(url, dest, headers)
        if ok:
            return DownloadResult(doi, slug, True, dest, label, msg)
        last_error = f"{label}: {msg}"
        time.sleep(0.5)

    if dest.exists():
        dest.unlink()

    if needs_human_handoff(last_error):
        landing = infer_referer(candidates[0][1]) if candidates else f"https://doi.org/{doi}"
        print(format_human_handoff(slug, landing), file=sys.stderr)

    return DownloadResult(doi, slug, False, None, "", last_error)


def load_paper_targets(papers_dir: Path, status_filter: Optional[str]) -> List[Tuple[str, str, str]]:
    """Return list of (slug, doi, status) from papers/*.md frontmatter."""
    targets: List[Tuple[str, str, str]] = []
    for md_path in sorted(papers_dir.glob("*.md")):
        if md_path.stem.startswith("_"):
            continue
        meta = parse_frontmatter(md_path.read_text(encoding="utf-8"))
        doi = normalize_doi(meta.get("doi", ""))
        status = meta.get("status", "")
        if not doi:
            continue
        if status_filter and status != status_filter:
            continue
        targets.append((md_path.stem, doi, status))
    return targets


def run_ingest(pdf_path: Path, output_dir: Path) -> None:
    from convert_pdf_to_markdown import convert_pdf_to_markdown

    md_path, images = convert_pdf_to_markdown(pdf_path, output_dir=output_dir)
    print(f"   📄 Ingested: {md_path} ({len(images)} image(s))", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download OA PDFs for literature grounding (OpenAlex + Semantic Scholar)."
    )
    parser.add_argument("--doi", help="DOI to download (e.g. 10.1145/2700648.2809841)")
    parser.add_argument("--slug", help="Output filename stem (default: derived from DOI)")
    parser.add_argument(
        "--paper-md",
        type=Path,
        help="Read DOI and slug from literature/papers/<slug>.md frontmatter",
    )
    parser.add_argument(
        "--papers-dir",
        type=Path,
        help="Batch mode: download for all *.md in dir (use with --status-filter)",
    )
    parser.add_argument(
        "--status-filter",
        default="abstract-only",
        help="Batch mode: only papers with this frontmatter status (default: abstract-only)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("docs/literature/papers/_downloads"),
        help="Directory for downloaded PDFs",
    )
    parser.add_argument("--dry-run", action="store_true", help="Resolve URLs only; do not download")
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="After download, run convert_pdf_to_markdown.py into papers dir (parent of _downloads)",
    )
    parser.add_argument("--config", type=Path, help="literature_providers.json path")
    args = parser.parse_args()

    config_path = args.config or (Path(__file__).parent.parent / "config" / "literature_providers.json")
    config = load_config(config_path)

    try:
        contact_email = require_contact_email(config)
    except ContactEmailError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    headers = build_request_headers(contact_email)

    jobs: List[Tuple[str, str]] = []

    if args.paper_md:
        text = args.paper_md.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)
        doi = normalize_doi(meta.get("doi", ""))
        slug = args.paper_md.stem
        if not doi:
            print(f"❌ No DOI in frontmatter: {args.paper_md}", file=sys.stderr)
            sys.exit(1)
        jobs.append((slug, doi))
    elif args.doi:
        slug = args.slug or normalize_doi(args.doi).replace("/", "-")
        jobs.append((slug, normalize_doi(args.doi)))
    elif args.papers_dir:
        for slug, doi, status in load_paper_targets(args.papers_dir, args.status_filter):
            jobs.append((slug, doi))
        if not jobs:
            print(f"ℹ️  No papers with status={args.status_filter!r} and DOI in {args.papers_dir}")
            sys.exit(0)
    else:
        parser.error("One of --doi, --paper-md, or --papers-dir is required")

    papers_parent = args.output_dir.parent if args.output_dir.name == "_downloads" else args.output_dir

    failures = 0
    for slug, doi in jobs:
        print(f"📥 {slug} (DOI {doi})", file=sys.stderr)
        result = download_for_doi(doi, slug, args.output_dir, headers, dry_run=args.dry_run)
        if result.success:
            print(f"✅ {slug}: {result.source} — {result.message}")
            if args.ingest and result.pdf_path and not args.dry_run:
                run_ingest(result.pdf_path, papers_parent)
        else:
            failures += 1
            print(f"❌ {slug}: {result.message}", file=sys.stderr)

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
