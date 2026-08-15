#!/usr/bin/env python3
"""
User Preferences & Native Language Configuration Manager.
Uses ONLY Python standard library.
"""

import sys
import json
import argparse
from pathlib import Path

DEFAULT_PREFERENCES_PATH = Path(__file__).parent.parent / "config" / "user_preferences.json"

DEFAULT_PREFERENCES = {
    "native_language": "Japanese",
    "language_code": "ja",
    "translation_style": "academic_formal",
    "preserve_original_terms": True,
    "output_mode": "bilingual_parallel"
}

def load_user_preferences(config_path: Path = DEFAULT_PREFERENCES_PATH) -> dict:
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                merged = DEFAULT_PREFERENCES.copy()
                merged.update(data)
                return merged
        except Exception as e:
            print(f"Warning: Could not parse {config_path}: {e}", file=sys.stderr)
            
    return DEFAULT_PREFERENCES.copy()

def save_user_preferences(prefs: dict, config_path: Path = DEFAULT_PREFERENCES_PATH) -> bool:
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving preferences to {config_path}: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Manage user language and translation preferences.")
    parser.add_argument("--show", action="store_true", help="Display current user preferences")
    parser.add_argument("--set-language", help="Set native language name (e.g. Japanese, English, German, French)")
    parser.add_argument("--set-code", help="Set native language ISO code (e.g. ja, en, de, fr)")
    parser.add_argument("--set-style", choices=["academic_formal", "plain", "bilingual_parallel"], help="Set translation output style")
    parser.add_argument("--config", help="Path to custom preferences JSON file")
    
    args = parser.parse_args()
    config_path = Path(args.config) if args.config else DEFAULT_PREFERENCES_PATH
    
    prefs = load_user_preferences(config_path)
    
    updated = False
    if args.set_language:
        prefs["native_language"] = args.set_language
        updated = True
    if args.set_code:
        prefs["language_code"] = args.set_code
        updated = True
    if args.set_style:
        prefs["translation_style"] = args.set_style
        updated = True
        
    if updated:
        if save_user_preferences(prefs, config_path):
            print(f"✅ Successfully updated preferences in {config_path}:")
        else:
            sys.exit(1)
            
    print(json.dumps(prefs, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
