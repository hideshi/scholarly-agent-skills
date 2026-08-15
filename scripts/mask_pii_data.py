#!/usr/bin/env python3
"""
PII Anonymization & Data Masking Script for Academic Research Data.
Masks emails, phone numbers, postal codes, SSNs/IDs, honorific-based names, and custom names in research data.
Uses ONLY Python standard library.
"""

import sys
import re
import json
import argparse
from pathlib import Path

# Common Regex Patterns for PII
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
# Japanese & International Phone Numbers
PHONE_REGEX = r'\b(?:0\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{3,4}|\+?\d{1,3}[-.\s]?\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{3,4})\b'
POSTAL_JP_REGEX = r'〒\s*\d{3}-\d{4}'
MYNUMBER_SSN_REGEX = r'\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b|\b\d{3}-\d{2}-\d{4}\b'

# Honorific-based Name Detection Regex
# Japanese: 山田氏, 佐藤教授, 鈴木代表, 田中博士
HONORIFIC_JP_REGEX = r'([一-龠]{1,4}|[ァ-ヶ]{2,8}|[A-Za-z]{1,15})\s*(氏|様|先生|教授|代表|部長|課長|専務|社長|常務|理事|委員|博士|殿)'

# English: Mr. Smith, Ms. Davis, Dr. Watson, Prof. John Davis
HONORIFIC_EN_REGEX = r'\b(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|President|Director|Chairman|Minister)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'


def load_name_mapping_file(file_path: Path) -> dict:
    """Load name replacements from a JSON or Key-Value text mapping file."""
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"Mapping file not found: {file_path}")

    content = file_path.read_text(encoding='utf-8').strip()
    if not content:
        return {}

    # Try parsing as JSON first
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except json.JSONDecodeError:
        pass

    # Parse as Key-Value text lines (e.g. Original=Masked)
    name_map = {}
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            if "=" in line:
                k, v = line.split("=", 1)
                name_map[k.strip()] = v.strip()
            else:
                name_map[line] = f"[ANONYMIZED_{len(name_map)+1}]"
    return name_map


def mask_pii_text(text: str, name_replacements: dict = None, auto_mask_honorifics: bool = True) -> str:
    """Mask sensitive PII in text string."""
    masked = text
    
    # 1. Custom Name Replacements (highest priority)
    if name_replacements:
        for name, replacement in name_replacements.items():
            if name.strip():
                masked = re.sub(re.escape(name.strip()), replacement.strip(), masked)
                
    # 2. Email Masking
    masked = re.sub(EMAIL_REGEX, '[EMAIL_MASKED]', masked)
    
    # 3. Japanese Postal Code (with 〒) Masking
    masked = re.sub(POSTAL_JP_REGEX, '[POSTAL_MASKED]', masked)
    
    # 4. SSN / MyNumber / Card ID Masking
    masked = re.sub(MYNUMBER_SSN_REGEX, '[ID_NUM_MASKED]', masked)
    
    # 5. Phone Number Masking
    masked = re.sub(PHONE_REGEX, '[PHONE_MASKED]', masked)
    
    # 6. Automatic Honorific Name Masking (Japanese & English)
    if auto_mask_honorifics:
        # Japanese Honorifics
        def replace_jp_name(m):
            name_part = m.group(1)
            suffix = m.group(2)
            # Skip short common words
            if name_part in ("本", "全", "各", "同", "現", "元", "新", "旧"):
                return m.group(0)
            return f"[NAME_MASKED]{suffix}"
            
        masked = re.sub(HONORIFIC_JP_REGEX, replace_jp_name, masked)
        
        # English Honorifics
        def replace_en_name(m):
            prefix = m.group(1)
            return f"{prefix} [NAME_MASKED]"
            
        masked = re.sub(HONORIFIC_EN_REGEX, replace_en_name, masked)
        
    return masked

def anonymize_file(input_path: Path, output_path: Path = None, name_replacements: dict = None, auto_mask_honorifics: bool = True) -> Path:
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    if output_path is None:
        output_dir = input_path.parent / "anonymized"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"anonymized_{input_path.name}"
    else:
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
    raw_content = input_path.read_text(encoding='utf-8', errors='ignore')
    sanitized_content = mask_pii_text(raw_content, name_replacements=name_replacements, auto_mask_honorifics=auto_mask_honorifics)
    output_path.write_text(sanitized_content, encoding='utf-8')
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Anonymize & Mask PII in research transcripts, surveys, and data files.")
    parser.add_argument("input_file", help="Path to input research file (txt, md, csv, json)")
    parser.add_argument("--output", "-o", help="Path to save anonymized output file")
    parser.add_argument("--names-file", "-f", help="Path to JSON or Key-Value file containing name replacements (recommended for privacy)")
    parser.add_argument("--names", "-n", nargs="+", help="[Deprecated / Warning] Names to replace in format OriginalName=MaskedName (CLI args may leak PII to process logs)")
    parser.add_argument("--no-auto-honorifics", action="store_true", help="Disable automatic honorific-based name masking (e.g. 〇〇氏, Dr. 〇〇)")
    
    args = parser.parse_args()
    
    name_map = {}

    if args.names_file:
        name_map.update(load_name_mapping_file(Path(args.names_file)))

    if args.names:
        print(
            "⚠️ Warning: Passing PII directly via CLI arguments (--names) may leak sensitive data into shell history or process listings. "
            "Consider using --names-file mapping.json instead.",
            file=sys.stderr
        )
        for pair in args.names:
            if '=' in pair:
                k, v = pair.split('=', 1)
                name_map[k] = v
            else:
                name_map[pair] = f"[ANONYMIZED_{len(name_map)+1}]"
                
    try:
        out_file = anonymize_file(Path(args.input_file), output_path=args.output, name_replacements=name_map, auto_mask_honorifics=not args.no_auto_honorifics)
        print(f"✅ Successfully anonymized PII research data:")
        print(f"   📄 Output File: {out_file}")
    except Exception as e:
        print(f"❌ Error anonymizing file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
