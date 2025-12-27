#!/usr/bin/env python3
"""
Test: OCR Settings
Tests the OCR enable/disable functionality in conversion scripts.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
import test_config


def test_docling_v5_no_ocr_option():
    """Test that docling_v5_convert.py accepts --no-ocr option"""
    script_path = test_config.RESOURCES_PYTHON / "docling_v5_convert.py"
    python = test_config.get_production_python("docling")
    
    if not python.exists():
        test_config.print_result(False, "Docling venv not found, skipping")
        return True  # Skip
    
    result = subprocess.run(
        [str(python), str(script_path), "--help"],
        capture_output=True,
        text=True
    )
    
    has_no_ocr = "--no-ocr" in result.stdout
    test_config.print_result(has_no_ocr, "--no-ocr option in docling_v5_convert.py help")
    
    if not has_no_ocr:
        print(f"  Help output: {result.stdout[:500]}")
    
    return has_no_ocr


def test_docling_v5_script_code():
    """Test that docling_v5_convert.py code handles enable_ocr parameter"""
    script_path = test_config.RESOURCES_PYTHON / "docling_v5_convert.py"
    content = script_path.read_text(encoding='utf-8')
    
    checks = [
        ("enable_ocr" in content, "enable_ocr parameter exists"),
        ("pipeline_options.do_ocr = enable_ocr" in content, "do_ocr controlled by enable_ocr"),
        ("if enable_ocr:" in content, "OCR options conditional on enable_ocr"),
        ("args.no_ocr" in content, "args.no_ocr parsed"),
    ]
    
    all_ok = True
    for ok, msg in checks:
        test_config.print_result(ok, msg)
        all_ok = all_ok and ok
    
    return all_ok


def test_docling_cli_no_ocr_option():
    """Test that Docling CLI supports --no-ocr or --ocr false option"""
    python = test_config.get_production_python("docling")
    
    if not python.exists():
        test_config.print_result(False, "Docling venv not found, skipping")
        return True  # Skip
    
    venv = test_config.get_production_venv("docling")
    docling_cli = venv / "Scripts" / "docling.exe"
    
    if not docling_cli.exists():
        test_config.print_result(False, "Docling CLI not found, skipping")
        return True  # Skip
    
    result = subprocess.run(
        [str(docling_cli), "--help"],
        capture_output=True,
        text=True
    )
    
    # Check if there's a way to disable OCR
    help_text = result.stdout.lower()
    has_no_ocr = "--no-ocr" in help_text or "--ocr" in help_text
    
    test_config.print_result(has_no_ocr, "Docling CLI has OCR control option")
    
    if not has_no_ocr:
        print(f"  Help output:\n{result.stdout}")
    
    return has_no_ocr


def test_conversion_service_passes_ocr_option():
    """Test that ConversionService.cs passes OCR options correctly"""
    cs_path = Path(test_config.PROJECT_ROOT) / "Services" / "ConversionService.cs"
    content = cs_path.read_text(encoding='utf-8')
    
    checks = [
        # RunRapidOcrV5Async checks
        ("!options.EnableOcr" in content and "--no-ocr" in content, 
         "RunRapidOcrV5Async passes --no-ocr"),
        
        # RunDoclingAsync should also handle OCR off
        # Currently it only adds OCR options when EnableOcr=true, but doesn't explicitly disable
    ]
    
    all_ok = True
    for ok, msg in checks:
        test_config.print_result(ok, msg)
        all_ok = all_ok and ok
    
    # Additional check: Does RunDoclingAsync need explicit OCR disable?
    # Check directly if --no-ocr appears in an else block after EnableOcr check
    # Look for pattern: else { ... --no-ocr
    import re
    pattern = r'else\s*\{[^}]*--no-ocr'
    has_ocr_disable = bool(re.search(pattern, content, re.DOTALL))
    
    # Also check simpler pattern
    if not has_ocr_disable:
        has_ocr_disable = 'else' in content and '--no-ocr' in content and 'Explicitly disable OCR' in content
    
    test_config.print_result(has_ocr_disable, "RunDoclingAsync explicitly disables OCR when EnableOcr=false")
    all_ok = all_ok and has_ocr_disable
    
    return all_ok


def main(quick=False):
    """Run all tests"""
    test_config.print_header("Test: OCR Settings")
    
    all_passed = True
    all_passed &= test_docling_v5_no_ocr_option()
    all_passed &= test_docling_v5_script_code()
    all_passed &= test_docling_cli_no_ocr_option()
    all_passed &= test_conversion_service_passes_ocr_option()
    
    print()
    if all_passed:
        print("[PASSED] All OCR settings tests passed")
    else:
        print("[FAILED] Some tests failed - OCR settings need fixing")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
