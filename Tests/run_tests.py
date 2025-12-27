#!/usr/bin/env python3
"""
MarkBridge Test Runner
Runs all tests in sequence and reports results.

Usage:
    python run_tests.py           # Run all tests
    python run_tests.py --quick   # Quick tests only (skip slow conversion tests)
"""

import sys
import time
import argparse
import importlib.util
from pathlib import Path

# Import test config
import test_config


def load_test_module(path):
    """Load a test module from path"""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_test(test_path, quick=False):
    """Run a single test and return (success, elapsed_time)"""
    print(f"\n{'='*60}")
    print(f" Running: {test_path.name}")
    print('='*60)
    
    start = time.time()
    try:
        module = load_test_module(test_path)
        
        # Check for main or run function
        if hasattr(module, 'main'):
            result = module.main(quick=quick) if 'quick' in str(module.main.__code__.co_varnames) else module.main()
        elif hasattr(module, 'run'):
            result = module.run(quick=quick) if 'quick' in str(module.run.__code__.co_varnames) else module.run()
        else:
            print(f"  Warning: No main() or run() function found")
            result = True
            
        elapsed = time.time() - start
        return (result is None or result), elapsed
        
    except Exception as e:
        elapsed = time.time() - start
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return False, elapsed


def main():
    parser = argparse.ArgumentParser(description='MarkBridge Test Runner')
    parser.add_argument('--quick', action='store_true', help='Quick tests only')
    parser.add_argument('tests', nargs='*', help='Specific tests to run')
    args = parser.parse_args()
    
    print("="*60)
    print(" MarkBridge Test Runner")
    print("="*60)
    print(f" Python: {sys.executable}")
    print(f" Tests Dir: {test_config.TESTS_DIR}")
    
    # Find tests
    if args.tests:
        test_files = [Path(t) for t in args.tests]
    else:
        test_files = sorted(test_config.TESTS_DIR.glob("test_*.py"))
        # Exclude test_config.py
        test_files = [f for f in test_files if f.name != "test_config.py"]
    
    if not test_files:
        print("\n  No tests found.")
        return
    
    print(f" Found {len(test_files)} test(s)")
    
    # Run tests
    results = []
    for test_path in test_files:
        success, elapsed = run_test(test_path, quick=args.quick)
        results.append((test_path.name, success, elapsed))
    
    # Summary
    print("\n" + "="*60)
    print(" Summary")
    print("="*60)
    
    passed = sum(1 for _, s, _ in results if s)
    failed = len(results) - passed
    total_time = sum(e for _, _, e in results)
    
    for name, success, elapsed in results:
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {name} ({elapsed:.1f}s)")
    
    print(f"\n  Total: {passed}/{len(results)} passed, {failed} failed")
    print(f"  Time: {total_time:.1f}s")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
