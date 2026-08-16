#!/usr/bin/env python3
"""
Multi-Provider Literature Search Script for Humanities & Academic Research.
Supports arXiv, OpenAlex, Crossref, Semantic Scholar, and custom user-configured providers.
Uses ONLY Python standard library.
"""

import sys
import os
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time
from pathlib import Path

from contact_email import ContactEmailError, require_contact_email

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "literature_providers.json"

def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to parse config file {config_path}: {e}", file=sys.stderr)
            
    # Default fallback configuration
    return {
        "default_provider": "openalex",
        "contact_email": "",
        "providers": {
            "arxiv": {
                "name": "arXiv",
                "type": "arxiv_atom",
                "base_url": "https://export.arxiv.org/api/query",
                "enabled": True
            },
            "openalex": {
                "name": "OpenAlex",
                "type": "openalex_json",
                "base_url": "https://api.openalex.org/works",
                "enabled": True
            },
            "crossref": {
                "name": "Crossref",
                "type": "crossref_json",
                "base_url": "https://api.crossref.org/works",
                "enabled": True
            },
            "semanticscholar": {
                "name": "Semantic Scholar",
                "type": "semanticscholar_json",
                "base_url": "https://api.semanticscholar.org/graph/v1/paper/search",
                "enabled": True
            }
        }
    }

def build_user_agent(contact_email: str = "") -> str:
    if contact_email:
        return f"Scholarly-Agent-Skills/1.0 (mailto:{contact_email})"
    return "Scholarly-Agent-Skills/1.0"


def build_request_headers(contact_email: str = "", extra: dict = None) -> dict:
    headers = {"User-Agent": build_user_agent(contact_email)}
    if extra:
        headers.update(extra)
    return headers


def fetch_url(url: str, headers: dict = None) -> bytes:
    req_headers = headers or {"User-Agent": build_user_agent()}
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read()

def search_arxiv(base_url: str, query: str, max_results: int = 5, headers: dict = None) -> list:
    encoded_query = urllib.parse.quote(query)
    url = f"{base_url}?search_query={encoded_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    raw_xml = fetch_url(url, headers=headers)
    root = ET.fromstring(raw_xml)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    
    results = []
    for entry in root.findall('atom:entry', ns):
        arxiv_id = entry.find('atom:id', ns).text.split('/')[-1] if entry.find('atom:id', ns) is not None else ""
        title = entry.find('atom:title', ns).text.strip().replace('\n', ' ') if entry.find('atom:title', ns) is not None else ""
        published = entry.find('atom:published', ns).text[:10] if entry.find('atom:published', ns) is not None else ""
        summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ') if entry.find('atom:summary', ns) is not None else ""
        
        authors = []
        for author_node in entry.findall('atom:author', ns):
            name_node = author_node.find('atom:name', ns)
            if name_node is not None:
                authors.append(name_node.text)
                
        pdf_url = ""
        for link in entry.findall('atom:link', ns):
            if link.attrib.get('title') == 'pdf':
                pdf_url = link.attrib.get('href', '')
                
        results.append({
            'provider': 'arXiv',
            'id': arxiv_id,
            'title': title,
            'authors': authors,
            'published': published,
            'summary': summary,
            'url': pdf_url or f"https://arxiv.org/abs/{arxiv_id}"
        })
    return results

def search_openalex(base_url: str, query: str, max_results: int = 5, headers: dict = None) -> list:
    encoded_query = urllib.parse.quote(query)
    url = f"{base_url}?search={encoded_query}&per_page={max_results}"
    raw_json = fetch_url(url, headers=headers)
    data = json.loads(raw_json.decode('utf-8'))
    
    results = []
    for item in data.get('results', []):
        title = item.get('title') or 'Untitled'
        published = str(item.get('publication_year') or '')
        
        authors = []
        for authorship in item.get('authorships', []):
            author_name = authorship.get('author', {}).get('display_name')
            if author_name:
                authors.append(author_name)
                
        # Reconstruct inverted index abstract if available
        summary = "No abstract available"
        inv_abstract = item.get('abstract_inverted_index')
        if inv_abstract and isinstance(inv_abstract, dict):
            word_list = []
            for word, pos_list in inv_abstract.items():
                for pos in pos_list:
                    word_list.append((pos, word))
            word_list.sort(key=lambda x: x[0])
            summary = " ".join([w[1] for w in word_list])
            if len(summary) > 500:
                summary = summary[:497] + "..."

        url_link = item.get('doi') or (item.get('primary_location') or {}).get('landing_page_url') or item.get('id')
        pdf_url = (item.get('best_oa_location') or {}).get('pdf_url') or ''
        if not pdf_url:
            for loc in item.get('locations') or []:
                if loc.get('pdf_url'):
                    pdf_url = loc['pdf_url']
                    break
        
        results.append({
            'provider': 'OpenAlex',
            'id': item.get('id', '').split('/')[-1],
            'title': title,
            'authors': authors,
            'published': published,
            'summary': summary,
            'url': url_link,
            'pdf_url': pdf_url,
        })
    return results

def search_crossref(base_url: str, query: str, max_results: int = 5, headers: dict = None) -> list:
    encoded_query = urllib.parse.quote(query)
    url = f"{base_url}?query={encoded_query}&rows={max_results}"
    raw_json = fetch_url(url, headers=headers)
    data = json.loads(raw_json.decode('utf-8'))
    
    results = []
    items = data.get('message', {}).get('items', [])
    for item in items:
        title = " ".join(item.get('title', [])) if item.get('title') else 'Untitled'
        authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in item.get('author', [])]
        published = ""
        date_parts = item.get('published-print', {}).get('date-parts') or item.get('published-online', {}).get('date-parts')
        if date_parts and date_parts[0]:
            published = "-".join([str(p) for p in date_parts[0]])
            
        summary = item.get('abstract') or "No abstract provided in Crossref metadata"
        summary = re_sub_html(summary)
        if len(summary) > 500:
            summary = summary[:497] + "..."
            
        url_link = item.get('URL') or (f"https://doi.org/{item.get('DOI')}" if item.get('DOI') else '')
        
        results.append({
            'provider': 'Crossref',
            'id': item.get('DOI', ''),
            'title': title,
            'authors': authors,
            'published': published,
            'summary': summary,
            'url': url_link
        })
    return results

def search_semanticscholar(base_url: str, query: str, max_results: int = 5, headers: dict = None) -> list:
    encoded_query = urllib.parse.quote(query)
    url = f"{base_url}?query={encoded_query}&limit={max_results}&fields=title,authors,year,abstract,url,openAccessPdf"
    raw_json = fetch_url(url, headers=headers)
    data = json.loads(raw_json.decode('utf-8'))
    
    results = []
    for item in data.get('data', []):
        title = item.get('title') or 'Untitled'
        authors = [a.get('name') for a in item.get('authors', []) if a.get('name')]
        published = str(item.get('year') or '')
        summary = item.get('abstract') or "No abstract available"
        url_link = item.get('url') or ''
        pdf_url = (item.get('openAccessPdf') or {}).get('url') or ''
        
        results.append({
            'provider': 'SemanticScholar',
            'id': item.get('paperId', ''),
            'title': title,
            'authors': authors,
            'published': published,
            'summary': summary,
            'url': url_link,
            'pdf_url': pdf_url,
        })
    return results

def re_sub_html(text: str) -> str:
    import re
    return re.sub(r'<[^>]+>', '', text).strip()

def search_literature(query: str, provider_key: str = "all", max_results: int = 5, config_path: Path = DEFAULT_CONFIG_PATH) -> list:
    config = load_config(config_path)
    providers = config.get("providers", {})
    contact_email = require_contact_email(config)
    request_headers = build_request_headers(contact_email)
    s2_api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    
    all_results = []
    
    if provider_key == "all":
        target_providers = [k for k, v in providers.items() if v.get("enabled", True)]
    else:
        target_providers = [provider_key] if provider_key in providers else []
    
    # Track providers that need rate limiting
    rate_limited_types = {"arxiv_atom"}
    last_request_time = 0.0
        
    for p_key in target_providers:
        p_info = providers.get(p_key)
        if not p_info:
            continue
        p_type = p_info.get("type")
        base_url = p_info.get("base_url")
        req_headers = request_headers
        if p_type == "semanticscholar_json" and s2_api_key:
            req_headers = build_request_headers(contact_email, extra={"x-api-key": s2_api_key})
        
        # Apply rate limiting for arXiv (minimum 3-second interval per API policy)
        if p_type in rate_limited_types:
            elapsed = time.time() - last_request_time
            if elapsed < 3.0 and last_request_time > 0:
                time.sleep(3.0 - elapsed)
        
        try:
            if p_type == "arxiv_atom":
                res = search_arxiv(base_url, query, max_results=max_results, headers=req_headers)
            elif p_type == "openalex_json":
                res = search_openalex(base_url, query, max_results=max_results, headers=req_headers)
            elif p_type == "crossref_json":
                res = search_crossref(base_url, query, max_results=max_results, headers=req_headers)
            elif p_type == "semanticscholar_json":
                res = search_semanticscholar(base_url, query, max_results=max_results, headers=req_headers)
            else:
                print(f"Warning: Unknown provider type '{p_type}' for '{p_key}'", file=sys.stderr)
                res = []
            all_results.extend(res)
            last_request_time = time.time()
        except Exception as e:
            print(f"Error querying provider '{p_key}': {e}", file=sys.stderr)
    
    # Deduplicate by DOI when available (cross-provider results often overlap)
    all_results = _deduplicate_results(all_results)
            
    return all_results


def _deduplicate_results(results: list) -> list:
    """Remove duplicate papers using DOI matching. Non-DOI results are always kept."""
    seen_dois = set()
    deduplicated = []
    for paper in results:
        url = paper.get('url', '')
        # Extract DOI from URL if present
        doi = None
        if 'doi.org/' in url:
            doi = url.split('doi.org/')[-1].lower().strip()
        elif paper.get('id', '').startswith('10.'):
            doi = paper['id'].lower().strip()
        
        if doi:
            if doi in seen_dois:
                continue
            seen_dois.add(doi)
        
        deduplicated.append(paper)
    
    removed = len(results) - len(deduplicated)
    if removed > 0:
        print(f"ℹ️  Removed {removed} duplicate(s) via DOI matching.", file=sys.stderr)
    
    return deduplicated

def format_markdown(results: list) -> str:
    lines = ["# Multi-Provider Literature Search Results\n"]
    for idx, paper in enumerate(results, 1):
        authors_str = ", ".join(paper['authors'][:3]) + (" et al." if len(paper['authors']) > 3 else "")
        lines.append(f"### {idx}. [{paper['title']}]({paper['url']})")
        lines.append(f"- **Provider**: `{paper['provider']}` | **ID**: `{paper['id']}`")
        lines.append(f"- **Authors**: {authors_str}")
        lines.append(f"- **Published**: {paper['published']}")
        if paper.get('pdf_url'):
            lines.append(f"- **OA PDF**: {paper['pdf_url']}")
        lines.append(f"- **Abstract**: {paper['summary']}\n")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Search scholarly papers across multiple open-access providers.")
    parser.add_argument("--query", "-q", required=True, help="Search query string")
    parser.add_argument("--provider", "-p", default="all", help="Provider key (arxiv, openalex, crossref, semanticscholar, or all)")
    parser.add_argument("--max-results", "-m", type=int, default=5, help="Maximum results per provider")
    parser.add_argument("--format", "-f", choices=["json", "markdown"], default="markdown", help="Output format")
    parser.add_argument("--config", "-c", help="Custom JSON configuration file path")
    
    args = parser.parse_args()
    config_path = Path(args.config) if args.config else DEFAULT_CONFIG_PATH

    try:
        results = search_literature(args.query, provider_key=args.provider, max_results=args.max_results, config_path=config_path)
    except ContactEmailError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    
    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(results))

if __name__ == '__main__':
    main()
