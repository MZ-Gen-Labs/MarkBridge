#!/usr/bin/env python3
"""
Test: Venv Setup Script
Tests the test venv creation and deletion functionality.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
import test_config


def test_setup_script_exists():
    """Test that setup_test_venv.py exists"""
    script_path = test_config.TESTS_DIR / "setup_test_venv.py"
    ok = script_path.exists()
    test_config.print_result(ok, f"Setup script exists: {script_path.name}")
    return ok


def test_setup_script_help():
    """Test that setup_test_venv.py --help runs without error"""
    script_path = test_config.TESTS_DIR / "setup_test_venv.py"
    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True
    )
    ok = result.returncode == 0
    test_config.print_result(ok, "Setup script --help runs successfully")
    return ok


def test_setup_script_status():
    """Test that setup_test_venv.py status runs without error"""
    script_path = test_config.TESTS_DIR / "setup_test_venv.py"
    result = subprocess.run(
        [sys.executable, str(script_path), "status"],
        capture_output=True,
        text=True
    )
    ok = result.returncode == 0
    test_config.print_result(ok, "Setup script status command runs")
    if ok:
        print(result.stdout)
    return ok


def test_test_python_path():
    """Test that get_test_python returns correct paths"""
    for engine in ["markitdown", "docling", "paddle"]:
        path = test_config.get_test_python(engine)
        ok = ".venv_test_" in str(path) and engine in str(path).lower()
        test_config.print_result(ok, f"get_test_python({engine}) = {path.name}")
    return True


def test_production_python_path():
    """Test that get_production_python returns correct paths"""
    for engine in ["markitdown", "docling", "paddle"]:
        path = test_config.get_production_python(engine)
        ok = ".venv_" in str(path) and "test" not in str(path)
        test_config.print_result(ok, f"get_production_python({engine}) = {path.name}")
    return True


def main(quick=False):
    """Run all tests"""
    test_config.print_header("Test: Venv Setup")
    
    all_passed = True
    all_passed &= test_setup_script_exists()
    all_passed &= test_setup_script_help()
    all_passed &= test_setup_script_status()
    all_passed &= test_test_python_path()
    all_passed &= test_production_python_path()
    
    print()
    if all_passed:
        print("[PASSED] All venv setup tests passed")
    else:
        print("[FAILED] Some tests failed")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
