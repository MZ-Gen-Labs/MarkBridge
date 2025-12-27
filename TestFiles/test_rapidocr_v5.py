#!/usr/bin/env python3
"""
RapidOCR v5 Test Script
Tests environment, model download, and PDF conversion.

Uses the existing Docling venv at: %LOCALAPPDATA%/MarkBridge/.venv_docling

Run with:
  %LOCALAPPDATA%/MarkBridge/.venv_docling/Scripts/python.exe test_rapidocr_v5.py
"""

import os
import sys
import time
import traceback

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_PDF = os.path.join(SCRIPT_DIR, "ocr_mixed_test.pdf")
OUTPUT_MD = os.path.join(SCRIPT_DIR, "ocr_mixed_test_v5test.md")

# Model configuration (same as rapidocr_v5_convert.py)
HUGGINGFACE_REPO = "marsena/paddleocr-onnx-models"
MODEL_FILES = {
    "det": "PP-OCRv5_server_det_infer.onnx",
    "rec": "PP-OCRv5_server_rec_infer.onnx",
}
REC_CONFIG_FILE = "PP-OCRv5_server_rec_infer.yml"
REC_KEYS_FILE = "pp_ocrv5_server_keys.txt"


def get_models_dir():
    """Get the models directory"""
    local_app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    return os.path.join(local_app_data, 'MarkBridge', 'models', 'rapidocr_v5')


def print_header(title):
    """Print section header"""
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print('=' * 50)


def print_check(name, status, details=""):
    """Print check result"""
    icon = "OK" if status else "FAILED"
    if details:
        print(f"  [{icon}] {name}: {details}")
    else:
        print(f"  [{icon}] {name}")
    return status


def check_python_version():
    """Check Python version"""
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok = sys.version_info >= (3, 10) and sys.version_info < (3, 14)
    return print_check("Python version", ok, f"{version} (need 3.10-3.13)")


def check_packages():
    """Check required packages"""
    packages = {
        "rapidocr_onnxruntime": "from rapidocr_onnxruntime import RapidOCR",
        "huggingface_hub": "import huggingface_hub",
        "pymupdf": "import fitz",
        "pyyaml": "import yaml",
        "opencv": "import cv2",
        "numpy": "import numpy",
    }
    
    all_ok = True
    for name, import_stmt in packages.items():
        try:
            exec(import_stmt)
            print_check(name, True, "installed")
        except ImportError as e:
            print_check(name, False, str(e))
            all_ok = False
    
    return all_ok


def check_models():
    """Check if models are downloaded"""
    models_dir = get_models_dir()
    all_ok = True
    
    print(f"  Models dir: {models_dir}")
    
    for name, filename in MODEL_FILES.items():
        path = os.path.join(models_dir, filename)
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print_check(f"{name} model", True, f"{filename} ({size_mb:.1f} MB)")
        else:
            print_check(f"{name} model", False, f"Not found: {filename}")
            all_ok = False
    
    # Check dictionary
    keys_path = os.path.join(models_dir, REC_KEYS_FILE)
    if os.path.exists(keys_path):
        with open(keys_path, 'r', encoding='utf-8') as f:
            count = sum(1 for _ in f)
        print_check("Character dictionary", True, f"{count:,} characters")
    else:
        print_check("Character dictionary", False, f"Not found: {REC_KEYS_FILE}")
        all_ok = False
    
    return all_ok


def download_models():
    """Download models if not present"""
    print("\n  Downloading models...")
    
    try:
        from huggingface_hub import hf_hub_download
        import yaml
    except ImportError as e:
        print(f"  Error: Missing package - {e}")
        return False
    
    models_dir = get_models_dir()
    os.makedirs(models_dir, exist_ok=True)
    
    # Download ONNX models
    for name, filename in MODEL_FILES.items():
        target_path = os.path.join(models_dir, filename)
        if not os.path.exists(target_path):
            print(f"    Downloading {filename}...")
            hf_hub_download(
                repo_id=HUGGINGFACE_REPO,
                filename=filename,
                local_dir=models_dir
            )
            print(f"    Downloaded: {filename}")
    
    # Download and extract dictionary
    keys_path = os.path.join(models_dir, REC_KEYS_FILE)
    if not os.path.exists(keys_path):
        print(f"    Downloading {REC_CONFIG_FILE}...")
        hf_hub_download(
            repo_id=HUGGINGFACE_REPO,
            filename=REC_CONFIG_FILE,
            local_dir=models_dir
        )
        
        # Extract dictionary from YML
        yml_path = os.path.join(models_dir, REC_CONFIG_FILE)
        print(f"    Extracting character dictionary...")
        with open(yml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        char_dict = config.get('PostProcess', {}).get('character_dict', [])
        with open(keys_path, 'w', encoding='utf-8') as f:
            for char in char_dict:
                f.write(char + '\n')
        
        print(f"    Extracted {len(char_dict)} characters to {REC_KEYS_FILE}")
    
    return True


def test_engine_creation():
    """Test RapidOCR engine creation"""
    try:
        from rapidocr_onnxruntime import RapidOCR
        
        models_dir = get_models_dir()
        det_model = os.path.join(models_dir, MODEL_FILES["det"])
        rec_model = os.path.join(models_dir, MODEL_FILES["rec"])
        rec_keys = os.path.join(models_dir, REC_KEYS_FILE)
        
        print(f"  Creating RapidOCR engine...")
        print(f"    det_model: {det_model}")
        print(f"    rec_model: {rec_model}")
        print(f"    rec_keys: {rec_keys}")
        
        engine = RapidOCR(
            det_model_path=det_model,
            rec_model_path=rec_model,
            cls_model_path=None,
            rec_keys_path=rec_keys
        )
        
        return print_check("Engine creation", True, "Success")
    except Exception as e:
        print_check("Engine creation", False, str(e)[:200])
        traceback.print_exc()
        return False


def test_pdf_conversion():
    """Test PDF conversion"""
    if not os.path.exists(TEST_PDF):
        print_check("Test PDF exists", False, f"Not found: {TEST_PDF}")
        return False
    
    pdf_size = os.path.getsize(TEST_PDF) / 1024
    print_check("Test PDF exists", True, f"{os.path.basename(TEST_PDF)} ({pdf_size:.1f} KB)")
    
    try:
        import fitz
        import cv2
        import numpy as np
        from rapidocr_onnxruntime import RapidOCR
        
        # Create engine
        models_dir = get_models_dir()
        det_model = os.path.join(models_dir, MODEL_FILES["det"])
        rec_model = os.path.join(models_dir, MODEL_FILES["rec"])
        rec_keys = os.path.join(models_dir, REC_KEYS_FILE)
        
        engine = RapidOCR(
            det_model_path=det_model,
            rec_model_path=rec_model,
            cls_model_path=None,
            rec_keys_path=rec_keys
        )
        
        # Open PDF
        doc = fitz.open(TEST_PDF)
        print(f"\n  Processing {len(doc)} pages...")
        
        all_content = []
        total_regions = 0
        total_time = 0
        
        for i, page in enumerate(doc):
            start_time = time.time()
            
            # Render page to image
            pix = page.get_pixmap(dpi=150)
            img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            
            # Convert to RGB if needed
            if pix.n == 4:
                img_data = cv2.cvtColor(img_data, cv2.COLOR_RGBA2RGB)
            elif pix.n == 1:
                img_data = cv2.cvtColor(img_data, cv2.COLOR_GRAY2RGB)
            
            # Run OCR
            result, _ = engine(img_data)
            
            elapsed = time.time() - start_time
            total_time += elapsed
            
            if result:
                regions = len(result)
                total_regions += regions
                
                # Extract text
                lines = [f"## Page {i + 1}\n"]
                for item in result:
                    text = item[1]
                    lines.append(text)
                all_content.append("\n".join(lines))
                
                print(f"    Page {i+1}: {regions} text regions ({elapsed:.1f}s)")
            else:
                print(f"    Page {i+1}: No text detected ({elapsed:.1f}s)")
        
        doc.close()
        
        # Write output
        final_content = "\n\n---\n\n".join(all_content)
        with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        output_size = os.path.getsize(OUTPUT_MD) / 1024
        print_check("Conversion complete", True, 
                   f"{total_regions} regions, {total_time:.1f}s total, {output_size:.1f} KB output")
        
        # Check for Japanese text
        japanese_chars = sum(1 for c in final_content if '\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff')
        total_chars = len(final_content.replace('\n', '').replace(' ', ''))
        if total_chars > 0:
            jp_ratio = japanese_chars / total_chars * 100
            print(f"  Japanese content: {jp_ratio:.1f}%")
        
        return True
        
    except Exception as e:
        print_check("Conversion", False, str(e)[:200])
        traceback.print_exc()
        return False


def main():
    print("=" * 50)
    print(" RapidOCR v5 Test Suite")
    print("=" * 50)
    print(f" Python: {sys.executable}")
    print(f" Working dir: {SCRIPT_DIR}")
    
    all_passed = True
    
    # Phase 1: Environment Check
    print_header("Phase 1: Environment Check")
    
    if not check_python_version():
        print("\n  ERROR: Python version not compatible.")
        print("  RapidOCR requires Python 3.10-3.13")
        print("  Current:", sys.version)
        sys.exit(1)
    
    if not check_packages():
        print("\n  ERROR: Some packages are missing.")
        print("  Please install RapidOCR v5 via Settings in the MarkBridge app.")
        sys.exit(1)
    
    # Phase 2: Model Check
    print_header("Phase 2: Model Check")
    
    if not check_models():
        print("\n  Models not found. Attempting to download...")
        if not download_models():
            all_passed = False
            sys.exit(1)
        
        # Re-check
        print("\n  Re-checking models...")
        if not check_models():
            all_passed = False
            sys.exit(1)
    
    # Phase 3: Engine Test
    print_header("Phase 3: Engine Test")
    
    if not test_engine_creation():
        all_passed = False
        sys.exit(1)
    
    # Phase 4: Conversion Test
    print_header("Phase 4: Conversion Test")
    
    if not test_pdf_conversion():
        all_passed = False
    
    # Summary
    print_header("Summary")
    if all_passed:
        print("  All tests passed!")
        print(f"\n  Output file: {OUTPUT_MD}")
        print("  Please review the output for OCR accuracy.")
    else:
        print("  Some tests failed. See above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
