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


def test_docling_cli_referenced_conversion():
    """Test actual conversion with referenced image mode using Docling CLI"""
    python = test_config.get_production_python("docling")
    
    if not python.exists():
        test_config.print_result(False, "Docling venv not found, skipping conversion test")
        return True  # Skip
    
    venv = test_config.get_production_venv("docling")
    docling_cli = venv / "Scripts" / "docling.exe"
    
    if not docling_cli.exists():
        test_config.print_result(False, "Docling CLI not found, skipping")
        return True  # Skip
    
    # Check if fixture exists
    fixture_path = test_config.FIXTURES_DIR / "ocr_mixed_test.pdf"
    if not fixture_path.exists():
        test_config.print_result(False, f"Fixture not found: {fixture_path}")
        return True  # Skip
    
    # Create temp output directory
    output_dir = test_config.ensure_output_dir()
    output_file = output_dir / "test_image_export_referenced.md"
    
    # Run Docling with referenced image mode
    test_config.print_result(True, "Running Docling CLI with --image-export-mode referenced...")
    
    result = subprocess.run(
        [
            str(docling_cli),
            str(fixture_path),
            "--to", "md",
            "--output", str(output_dir),
            "--no-ocr",
            "--image-export-mode", "referenced",
            "--device", "cpu"
        ],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    # Check if conversion succeeded
    expected_output = output_dir / "ocr_mixed_test.md"
    if not expected_output.exists():
        test_config.print_result(False, f"Output file not created: {expected_output}")
        print(f"  stderr: {result.stderr[:500]}")
        return False
    
    # Read output and check for image links
    content = expected_output.read_text(encoding='utf-8')
    
    # Check for image syntax in markdown
    import re
    image_links = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
    has_image_links = len(image_links) > 0
    
    test_config.print_result(has_image_links, f"Markdown contains image links: {len(image_links)} found")
    
    if has_image_links:
        for alt, path in image_links[:3]:  # Show first 3
            print(f"    ![{alt[:20]}...]({path})")
    else:
        print(f"  No image links found in output.")
        print(f"  Output preview: {content[:500]}")
    
    # Check if image files were created
    image_files = list(output_dir.glob("*.png")) + list(output_dir.glob("*.jpg"))
    images_subdir = output_dir / "images"
    if images_subdir.exists():
        image_files.extend(images_subdir.glob("*.png"))
        image_files.extend(images_subdir.glob("*.jpg"))
    
    has_image_files = len(image_files) > 0
    test_config.print_result(has_image_files, f"Image files created: {len(image_files)} found")
    
    if has_image_files:
        for img in image_files[:3]:  # Show first 3
            print(f"    {img.name}")
    
    return has_image_links or has_image_files  # At least one should be true


def main(quick=False):
    """Run all tests"""
    test_config.print_header("Test: Image Export")
    
    all_passed = True
    all_passed &= test_docling_script_exists()
    all_passed &= test_docling_script_help()
    all_passed &= test_referenced_mode_logic()
    all_passed &= test_image_mode_choices()
    
    if not quick:
        all_passed &= test_docling_cli_referenced_conversion()
    
    print()
    if all_passed:
        print("[PASSED] All image export tests passed")
    else:
        print("[FAILED] Some tests failed")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
