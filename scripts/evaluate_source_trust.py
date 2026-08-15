#!/usr/bin/env python3
"""
Evaluate the trustworthiness and academic validity of information sources.
Default-Deny Policy: ONLY sources explicitly listed in Tier 1 / Tier 2 (standard + custom config) are permitted.
All other unlisted sources are classified as Tier 3 (REJECTED).
"""

import sys
import json
import argparse
import urllib.parse
from pathlib import Path
from typing import Dict, List, Tuple

# Built-in Standard Approved Domain Patterns & Authorities
STANDARD_TIER_1 = [
    # Peer-reviewed & Academic Repositories
    "openalex.org", "arxiv.org", "crossref.org", "semanticscholar.org",
    "sciencedirect.com", "springer.com", "wiley.com", "jstor.org",
    "nber.org", "repec.org", "tandfonline.com", "ieee.org",
    # Official International Organizations
    "worldbank.org", "imf.org", "adb.org", "un.org", "oecd.org", "who.int",
    # Official National Statistics & Central Banks
    "psa.gov.ph", "bsp.gov.ph", "stat.go.jp", "boj.or.jp", "federalreserve.gov"
]

STANDARD_TIER_2 = [
    # Official Government Ministries & Public Research Institutes
    "pids.gov.ph", "dswd.gov.ph", "nea.gov.ph", "rieti.go.jp", "brookings.edu", "rand.org",
    # Specific Country/Academic TLD suffixes and patterns
    ".gov.ph", ".go.jp", ".gov", ".edu", ".ac.uk", ".ac.jp", ".edu.au"
]


def extract_hostname(url_or_domain: str) -> str:
    """Extract clean hostname stripped of protocol, userinfo, port, and trailing dots."""
    cleaned = url_or_domain.strip().lower()
    if cleaned.startswith(("http://", "https://")):
        parsed = urllib.parse.urlparse(cleaned)
        # Disallow domain-like userinfo (e.g. http://evil.com@arxiv.org) to prevent phishing
        if parsed.username and "." in parsed.username:
            return ""
        host = parsed.hostname or ""
    else:
        if "@" in cleaned and "." in cleaned.split("@")[0]:
            return ""
        host = cleaned.split("/")[0].split("@")[-1].split(":")[0]
    return host.rstrip(".")


def domain_matches(host: str, pattern: str) -> bool:
    """
    Strict domain matching:
    - Exact match (e.g. host == 'arxiv.org')
    - Strict subdomain match with dot boundary (e.g. host.endswith('.arxiv.org'))
    - TLD suffix match if pattern starts with '.' (e.g. pattern == '.gov' matches 'dswd.gov')
    """
    pattern = pattern.strip().lower()
    if not host or not pattern:
        return False

    if pattern.startswith("."):
        return host.endswith(pattern) or host == pattern.lstrip(".")

    return host == pattern or host.endswith("." + pattern)


def load_custom_trusted_domains(config_path: Path = None) -> Tuple[List[str], List[str]]:
    """Load custom trusted domains from config/trusted_domains.json if present."""
    custom_tier_1 = []
    custom_tier_2 = []

    candidate_paths = []
    if config_path:
        candidate_paths.append(config_path)
    else:
        cwd = Path.cwd()
        candidate_paths.extend([
            cwd / "config" / "trusted_domains.json",
            cwd / ".scholarly-agent-skills" / "config" / "trusted_domains.json",
            Path(__file__).parent.parent / "config" / "trusted_domains.json"
        ])

    for path in candidate_paths:
        if path and path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                custom_tier_1.extend(data.get("tier_1", []))
                custom_tier_2.extend(data.get("tier_2", []))
                break
            except Exception as e:
                print(f"Warning: Error reading custom config {path}: {e}", file=sys.stderr)

    return custom_tier_1, custom_tier_2


def evaluate_source(url_or_domain: str, config_path: Path = None) -> Tuple[int, str, str]:
    """
    Evaluate a URL or domain string using Default-Deny policy.
    Returns: (Tier_Level [1, 2, 3], Classification_Label, Reason)
    """
    host = extract_hostname(url_or_domain)
    if not host:
        return (
            3,
            "REJECTED (Invalid or Spoofed Host)",
            f"Could not parse valid hostname from '{url_or_domain}' or detected URL spoofing pattern."
        )

    # Load custom domain additions
    custom_t1, custom_t2 = load_custom_trusted_domains(config_path)
    all_tier_1 = STANDARD_TIER_1 + custom_t1
    all_tier_2 = STANDARD_TIER_2 + custom_t2

    # Check Tier 1 Allowlist
    for t1 in all_tier_1:
        if domain_matches(host, t1):
            return (
                1,
                "APPROVED (Tier 1: Peer-Reviewed / International Official)",
                f"Domain '{host}' matches Tier 1 registry pattern '{t1}'."
            )

    # Check Tier 2 Allowlist
    for t2 in all_tier_2:
        if domain_matches(host, t2):
            return (
                2,
                "ACCEPTABLE (Tier 2: Official Government / Academic Institution)",
                f"Domain '{host}' matches Tier 2 registry pattern '{t2}'."
            )

    # Default-Deny: Anything not explicitly matched in Tier 1 or Tier 2 is REJECTED
    return (
        3,
        "REJECTED (Unlisted / Default-Deny)",
        f"Domain '{host}' is not in the approved Tier 1 or Tier 2 allowlists."
    )


def main():
    parser = argparse.ArgumentParser(description="Evaluate Academic Source Trustworthiness (Default-Deny Policy).")
    parser.add_argument("source", type=str, help="URL or domain string to evaluate")
    parser.add_argument("--config", type=Path, help="Path to custom config/trusted_domains.json")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")

    args = parser.parse_args()
    tier, label, reason = evaluate_source(args.source, config_path=args.config)

    res = {
        "source": args.source,
        "tier": tier,
        "classification": label,
        "reason": reason
    }

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        status_icon = "🟢" if tier == 1 else ("🟡" if tier == 2 else "🔴")
        print(f"{status_icon} [{label}]")
        print(f"  Source: {args.source}")
        print(f"  Reason: {reason}")

    if tier == 3:
        sys.exit(1)


if __name__ == "__main__":
    main()
