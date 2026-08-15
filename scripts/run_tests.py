#!/usr/bin/env python3
"""
Test Runner for Humanities Agent Skills.
Uses Python standard library (unittest) to discover and run all tests in tests/ directory.
"""

import sys
import unittest
from pathlib import Path

def main():
    repo_root = Path(__file__).parent.parent
    tests_dir = repo_root / "tests"
    
    print(f"🧪 Discovering and running unit tests in {tests_dir}...")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(tests_dir), pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("🎉 All unit tests passed!")
        sys.exit(0)
    else:
        print(f"💥 Unit tests failed with {len(result.failures)} failure(s) and {len(result.errors)} error(s).", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
