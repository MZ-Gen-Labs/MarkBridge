#!/usr/bin/env python3
"""
Test: Image Export
Tests the image export functionality of docling_v5_convert.py.
"""

import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
import test_config


def test_docling_script_exists():
    """Test that docling_v5_convert.py exists"""
    script_path = test_config.RESOURCES_PYTHON / "docling_v5_convert.py"
    ok = script_path.exists()
    test_config.print_result(ok, f"Docling script exists: {script_path.name}")
    return ok


def test_docling_script_help():
    """Test that docling_v5_convert.py --help runs without error"""
    script_path = test_config.RESOURCES_PYTHON / "docling_v5_convert.py"
    python = test_config.get_production_python("docling")
    
    if not python.exists():
        test_config.print_result(False, "Docling venv not found, skipping help test")
        return True  # Skip
    
    result = subprocess.run(
        [str(python), str(script_path), "--help"],
        capture_output=True,
        text=True
    )
    ok = result.returncode == 0
    test_config.print_result(ok, "Docling script --help runs successfully")
    return ok


def test_referenced_mode_logic():
    """Test that referenced mode logic is present in script"""
    script_path = test_config.RESOURCES_PYTHON / "docling_v5_convert.py"
    content = script_path.read_text(encoding='utf-8')
    
    checks = [
        ('image_mode == "referenced"' in content, "Referenced mode check exists"),
        ('images_dir_name' in content, "Images directory naming exists"),
        ('picture.get_image' in content, "Picture image extraction exists"),
        ('table.get_image' in content, "Table image extraction exists"),
    ]
    
    all_ok = True
    for ok, msg in checks:
        test_config.print_result(ok, msg)
        all_ok = all_ok and ok
    
    return all_ok


def test_image_mode_choices():
    """Test that all image mode choices are available"""
    script_path = test_config.RESOURCES_PYTHON / "docling_v5_convert.py"
    content = script_path.read_text(encoding='utf-8')
    
    checks = [
        ("'placeholder'" in content, "Placeholder mode available"),
        ("'embedded'" in content, "Embedded mode available"),
        ("'referenced'" in content, "Referenced mode available"),
    ]
    
    all_ok = True
    for ok, msg in checks:
        test_config.print_result(ok, msg)
        all_ok = all_ok and ok
    
    return all_ok


def main(quick=False):
    """Run all tests"""
    test_config.print_header("Test: Image Export")
    
    all_passed = True
    all_passed &= test_docling_script_exists()
    all_passed &= test_docling_script_help()
    all_passed &= test_referenced_mode_logic()
    all_passed &= test_image_mode_choices()
    
    print()
    if all_passed:
        print("[PASSED] All image export tests passed")
    else:
        print("[FAILED] Some tests failed")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
