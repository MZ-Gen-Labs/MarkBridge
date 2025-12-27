#!/usr/bin/env python3
"""
Docling with PP-OCRv5 Integration Test
Tests the docling_v5_convert.py script which uses Docling pipeline
with RapidOCR configured to use PP-OCRv5 models.
"""

import sys
import time

# Import test config first
import test_config

# Now import main script
import docling_v5_convert


def main(quick=False):
    """Run Docling with PP-OCRv5 integration test"""
    test_config.print_header("Docling + PP-OCRv5 Integration Test")
    
    all_ok = True
    
    # Model check
    test_config.print_header("Phase 1: Model Check")
    if docling_v5_convert.check_models_exist():
        test_config.print_result(True, "All models present")
    else:
        test_config.print_result(False, "Models missing")
        print("  Downloading models...")
        docling_v5_convert.download_models_if_needed()
    
    if quick:
        test_config.print_header("Summary")
        print("  Quick mode - skipping conversion test")
        return True
    
    # Conversion test
    test_config.print_header("Phase 2: Conversion Test")
    
    test_pdf = test_config.get_fixture("ocr_mixed_test.pdf")
    output_dir = test_config.ensure_output_dir()
    output_file = output_dir / "docling_v5_test.md"
    
    print(f"  Input: {test_pdf}")
    print(f"  Output: {output_file}")
    
    start = time.time()
    try:
        docling_v5_convert.convert_document(
            str(test_pdf),
            str(output_file),
            use_gpu=False,
            force_ocr=False,
            image_mode="placeholder"
        )
        elapsed = time.time() - start
        
        if output_file.exists():
            size_kb = output_file.stat().st_size / 1024
            test_config.print_result(True, f"Conversion complete: {size_kb:.1f} KB in {elapsed:.1f}s")
            
            # Check content
            content = output_file.read_text(encoding='utf-8')
            
            # Check for table structure
            has_tables = '|' in content and '-|-' in content
            test_config.print_result(has_tables, f"Table structure: {'detected' if has_tables else 'NOT detected'}")
            if not has_tables:
                all_ok = False
            
            # Japanese content ratio
            jp_ratio = sum(1 for c in content if '\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff') / max(1, len(content.replace(' ', '').replace('\n', '')))
            print(f"  Japanese content: {jp_ratio*100:.1f}%")
        else:
            test_config.print_result(False, "Output file not created")
            all_ok = False
            
    except Exception as e:
        test_config.print_result(False, f"Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        all_ok = False
    
    # Summary
    test_config.print_header("Summary")
    if all_ok:
        print("  All tests passed!")
    else:
        print("  Some tests failed.")
    
    return all_ok


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args()
    
    success = main(quick=args.quick)
    sys.exit(0 if success else 1)
