#!/usr/bin/env python3
"""
Environment Diagnostic Test
Checks Python version, installed packages, and model availability.
"""

import sys
import os

# Import test config first
import test_config


def main(quick=False):
    """Run environment diagnostics"""
    test_config.print_header("Environment Diagnostic Test")
    print(f"  Python: {sys.executable}")
    print(f"  Version: {sys.version}")
    
    all_ok = True
    
    # Python version check
    test_config.print_header("Phase 1: Python Version")
    version = sys.version_info
    if 10 <= version.minor <= 13 and version.major == 3:
        test_config.print_result(True, f"Python {version.major}.{version.minor} (compatible)")
    else:
        test_config.print_result(False, f"Python {version.major}.{version.minor} (need 3.10-3.13)")
        all_ok = False
    
    # Package checks
    test_config.print_header("Phase 2: Required Packages")
    packages = [
        ("rapidocr_onnxruntime", "rapidocr_onnxruntime"),
        ("huggingface_hub", "huggingface_hub"),
        ("docling", "docling"),
        ("pymupdf", "fitz"),
        ("pyyaml", "yaml"),
        ("opencv", "cv2"),
        ("numpy", "numpy"),
    ]
    
    for name, import_name in packages:
        try:
            __import__(import_name)
            test_config.print_result(True, f"{name}: installed")
        except ImportError:
            test_config.print_result(False, f"{name}: NOT installed")
            all_ok = False
    
    # Model checks
    test_config.print_header("Phase 3: PP-OCRv5 Models")
    models_dir = test_config.MODELS_DIR / "rapidocr_v5"
    
    if models_dir.exists():
        det_model = models_dir / "PP-OCRv5_server_det_infer.onnx"
        rec_model = models_dir / "PP-OCRv5_server_rec_infer.onnx"
        keys_file = models_dir / "pp_ocrv5_server_keys.txt"
        
        for path, name in [(det_model, "det model"), (rec_model, "rec model"), (keys_file, "keys file")]:
            if path.exists():
                size_mb = path.stat().st_size / 1024 / 1024
                test_config.print_result(True, f"{name}: {size_mb:.1f} MB")
            else:
                test_config.print_result(False, f"{name}: NOT found")
                all_ok = False
    else:
        test_config.print_result(False, f"Models dir not found: {models_dir}")
        all_ok = False
    
    # Summary
    test_config.print_header("Summary")
    if all_ok:
        print("  All checks passed!")
    else:
        print("  Some checks failed. See above for details.")
    
    return all_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
