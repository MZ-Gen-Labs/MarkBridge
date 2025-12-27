#!/usr/bin/env python3
"""
Test script for docling_v5_convert.py
Tests Docling pipeline with PP-OCRv5 models for OCR.

Run with:
  %LOCALAPPDATA%/MarkBridge/.venv_docling/Scripts/python.exe test_docling_v5.py
"""

import os
import sys
import time

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCLING_V5_SCRIPT = os.path.join(os.path.dirname(SCRIPT_DIR), "Resources", "Python", "docling_v5_convert.py")
TEST_PDF = os.path.join(SCRIPT_DIR, "ocr_mixed_test.pdf")
OUTPUT_MD = os.path.join(SCRIPT_DIR, "ocr_mixed_test_docling_v5.md")


def print_header(title):
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print('=' * 50)


def main():
    print("=" * 50)
    print(" Docling with PP-OCRv5 Test")
    print("=" * 50)
    print(f" Python: {sys.executable}")
    print(f" Script: {DOCLING_V5_SCRIPT}")
    
    # Check if script exists
    script_path = DOCLING_V5_SCRIPT
    if not os.path.exists(script_path):
        print(f"\n[ERROR] Script not found: {script_path}")
        # Try alternative path (within TestFiles)
        alt_path = os.path.join(SCRIPT_DIR, "..", "Resources", "Python", "docling_v5_convert.py")
        if os.path.exists(alt_path):
            script_path = os.path.abspath(alt_path)
            print(f" Using alternative path: {script_path}")
        else:
            sys.exit(1)
    
    # Check test PDF
    if not os.path.exists(TEST_PDF):
        print(f"\n[ERROR] Test PDF not found: {TEST_PDF}")
        sys.exit(1)
    
    print(f" Test PDF: {TEST_PDF}")
    print(f" Output: {OUTPUT_MD}")
    
    # Import and run directly (same Python environment)
    print_header("Phase 1: Import docling_v5_convert")
    
    sys.path.insert(0, os.path.dirname(script_path))
    
    try:
        import docling_v5_convert
        print("  [OK] Module imported successfully")
    except ImportError as e:
        print(f"  [FAILED] Import error: {e}")
        sys.exit(1)
    
    # Check models
    print_header("Phase 2: Check Models")
    
    models_dir = docling_v5_convert.get_models_dir()
    print(f"  Models dir: {models_dir}")
    
    if docling_v5_convert.check_models_exist():
        print("  [OK] All models present")
    else:
        print("  Downloading models...")
        docling_v5_convert.download_models_if_needed()
        print("  [OK] Models downloaded")
    
    # Convert document
    print_header("Phase 3: Convert Document")
    
    start_time = time.time()
    
    try:
        docling_v5_convert.convert_document(
            TEST_PDF,
            OUTPUT_MD,
            use_gpu=False,
            force_ocr=False,
            image_mode="placeholder"
        )
        elapsed = time.time() - start_time
        print(f"  [OK] Conversion complete in {elapsed:.1f}s")
    except Exception as e:
        print(f"  [FAILED] Conversion error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Check output
    print_header("Phase 4: Verify Output")
    
    if os.path.exists(OUTPUT_MD):
        size_kb = os.path.getsize(OUTPUT_MD) / 1024
        print(f"  [OK] Output file: {OUTPUT_MD}")
        print(f"  [OK] Size: {size_kb:.1f} KB")
        
        # Show first 500 chars
        with open(OUTPUT_MD, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for table markers
        has_tables = '|' in content and '-|-' in content
        print(f"  Table structure detected: {'Yes' if has_tables else 'No'}")
        
        # Check for Japanese
        jp_chars = sum(1 for c in content if '\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff')
        total_chars = len(content.replace('\n', '').replace(' ', ''))
        if total_chars > 0:
            print(f"  Japanese content: {jp_chars / total_chars * 100:.1f}%")
        
        print("\n  === First 500 characters ===")
        print(content[:500])
    else:
        print(f"  [FAILED] Output file not created")
        sys.exit(1)
    
    # Summary
    print_header("Summary")
    print("  All tests passed!")
    print(f"  Output: {OUTPUT_MD}")


if __name__ == "__main__":
    main()
