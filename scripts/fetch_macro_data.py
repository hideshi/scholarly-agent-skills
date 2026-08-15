#!/usr/bin/env python3
"""
Fetch Macroeconomic & Social Indicators from World Bank Open Data API.
Zero-dependency script (uses standard library urllib.request & json).

Examples:
    python3 fetch_macro_data.py --country PH --indicators NY.GDP.MKTP.KD.ZG SI.POV.GINI --start 2000 --end 2024
    python3 fetch_macro_data.py --country PH --preset poverty --format markdown
"""

import sys
import json
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

from contact_email import ContactEmailError, require_contact_email

# Pre-defined indicator sets for academic research
PRESETS = {
    "poverty": {
        "NY.GDP.MKTP.KD.ZG": "GDP Growth (Annual %)",
        "SI.POV.DDAY": "Poverty Headcount Ratio ($2.15/day PPP %)",
        "SI.POV.GINI": "Gini Index",
        "BX.TRF.PWKR.DT.GD.ZS": "Personal Remittances Received (% of GDP)",
        "SL.AGR.EMPL.ZS": "Employment in Agriculture (% of total)",
        "SL.SRV.EMPL.ZS": "Employment in Services (% of total)",
    },
    "macro": {
        "NY.GDP.MKTP.KD.ZG": "GDP Growth (Annual %)",
        "NY.GDP.PCAP.KD": "GDP per Capita (constant 2015 US$)",
        "FP.CPI.TOTL.ZG": "Inflation, Consumer Prices (Annual %)",
    }
}


def build_user_agent(contact_email: str = "") -> str:
    if contact_email:
        return f"Scholarly-Agent-Skills/1.0 (mailto:{contact_email}; Academic Research Tool)"
    return "Scholarly-Agent-Skills/1.0 (Academic Research Tool)"


def fetch_indicator_data(country: str, indicator: str, start_year: int, end_year: int) -> List[Dict[str, Any]]:
    """Fetch indicator time series for a country from World Bank HTTPS API."""
    url = (
        f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        f"?date={start_year}:{end_year}&format=json&per_page=100"
    )
    contact_email = require_contact_email()
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": build_user_agent(contact_email)}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
                results = []
                for entry in data[1]:
                    results.append({
                        "year": entry.get("date"),
                        "value": entry.get("value"),
                        "indicator_id": indicator,
                        "indicator_name": entry.get("indicator", {}).get("value")
                    })
                return results
            elif isinstance(data, list) and len(data) >= 1 and isinstance(data[0], dict) and "message" in data[0]:
                msg = data[0]["message"]
                print(f"Warning: World Bank API returned error message for {indicator}: {msg}", file=sys.stderr)
    except urllib.error.URLError as e:
        print(f"Warning: Failed to fetch {indicator} for {country}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error parsing data for {indicator}: {e}", file=sys.stderr)
        
    return []


def aggregate_indicators(country: str, indicator_map: Dict[str, str], start_year: int, end_year: int) -> Dict[str, Dict[str, Any]]:
    """Fetch multiple indicators and aggregate by year."""
    aggregated: Dict[str, Dict[str, Any]] = {}
    
    for ind_id, label in indicator_map.items():
        records = fetch_indicator_data(country, ind_id, start_year, end_year)
        for rec in records:
            year = rec["year"]
            if year not in aggregated:
                aggregated[year] = {"Year": year}
            aggregated[year][label] = rec["value"]
            
    # Sort by year ascending
    sorted_years = sorted(aggregated.keys())
    return {y: aggregated[y] for y in sorted_years}


def format_as_markdown(data: Dict[str, Dict[str, Any]], indicator_labels: List[str], country: str, start_year: int, end_year: int) -> str:
    """Format aggregated dictionary as Markdown table with provenance header."""
    timestamp = datetime.now(timezone.utc).isoformat()
    provenance = f"<!-- Source: World Bank Open Data API (https://api.worldbank.org/v2/) | Country: {country} | Period: {start_year}-{end_year} | Retrieved: {timestamp} -->\n"

    headers = ["Year"] + indicator_labels
    lines = [provenance]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    for year, row in data.items():
        cols = [str(year)]
        for label in indicator_labels:
            val = row.get(label)
            if val is None:
                cols.append("N/A")
            elif isinstance(val, float):
                cols.append(f"{val:.2f}")
            else:
                cols.append(str(val))
        lines.append("| " + " | ".join(cols) + " |")
        
    return "\n".join(lines)


def format_as_csv(data: Dict[str, Dict[str, Any]], indicator_labels: List[str]) -> str:
    """Format aggregated dictionary as CSV string."""
    headers = ["Year"] + indicator_labels
    lines = [",".join(headers)]
    
    for year, row in data.items():
        cols = [str(year)]
        for label in indicator_labels:
            val = row.get(label)
            if val is None:
                cols.append("")
            else:
                cols.append(str(val))
        lines.append(",".join(cols))
        
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Fetch Macroeconomic Indicators from World Bank Open Data API.")
    parser.add_argument("--country", type=str, default="PH", help="ISO country code (default: PH)")
    parser.add_argument("--preset", type=str, choices=list(PRESETS.keys()), default="poverty", help="Predefined indicator preset")
    parser.add_argument("--indicators", nargs="+", help="Custom indicator IDs (e.g., NY.GDP.MKTP.KD.ZG SI.POV.GINI)")
    parser.add_argument("--start", type=int, default=2000, help="Start year (default: 2000)")
    parser.add_argument("--end", type=int, default=2024, help="End year (default: 2024)")
    parser.add_argument("--format", type=str, choices=["markdown", "csv", "json"], default="markdown", help="Output format")
    parser.add_argument("-o", "--output", type=Path, help="Output file path (optional)")

    args = parser.parse_args()

    try:
        require_contact_email()
    except ContactEmailError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if args.indicators:
        indicator_map = {ind: ind for ind in args.indicators}
    else:
        indicator_map = PRESETS[args.preset]

    print(f"🌐 Fetching World Bank HTTPS indicators for {args.country} ({args.start}-{args.end})...")
    aggregated = aggregate_indicators(args.country, indicator_map, args.start, args.end)
    indicator_labels = list(indicator_map.values())

    if args.format == "markdown":
        output_str = format_as_markdown(aggregated, indicator_labels, args.country, args.start, args.end)
    elif args.format == "csv":
        output_str = format_as_csv(aggregated, indicator_labels)
    else:
        output_str = json.dumps(aggregated, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_str, encoding="utf-8")
        print(f"✅ Saved data to {args.output}")
    else:
        print("\n" + output_str)


if __name__ == "__main__":
    main()
