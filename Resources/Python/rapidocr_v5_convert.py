#!/usr/bin/env python3
"""
RapidOCR v5 Conversion Script for MarkBridge
Uses PP-OCRv5 ONNX models for high-accuracy Japanese OCR
"""

import os
import sys
import argparse
import traceback
import tempfile
import shutil
import uuid

# Model repository and file names
HUGGINGFACE_REPO = "marsena/paddleocr-onnx-models"
MODEL_FILES = {
    "det": "PP-OCRv5_server_det_infer.onnx",
    "rec": "PP-OCRv5_server_rec_infer.onnx",
    # Note: cls model (PP-LCNet) is not used - incompatible input dimensions
}

# PP-OCRv5 server rec model config (contains 18K character dictionary)
REC_CONFIG_FILE = "PP-OCRv5_server_rec_infer.yml"
REC_KEYS_FILE = "pp_ocrv5_server_keys.txt"  # Extracted from YML

def get_models_dir():
    """Get the models directory for PP-OCRv5"""
    local_app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    return os.path.join(local_app_data, 'MarkBridge', 'models', 'rapidocr_v5')

def check_models_exist():
    """Check if all required models are downloaded"""
    models_dir = get_models_dir()
    for name, filename in MODEL_FILES.items():
        path = os.path.join(models_dir, filename)
        if not os.path.exists(path):
            return False
    # Also check for character dictionary (extracted from YML)
    keys_path = os.path.join(models_dir, REC_KEYS_FILE)
    if not os.path.exists(keys_path):
        return False
    return True

def extract_keys_from_yml(yml_path, output_path, on_progress=None):
    """Extract character dictionary from YML config file"""
    import yaml
    
    if on_progress:
        on_progress(f"Extracting character dictionary from {os.path.basename(yml_path)}...")
    
    with open(yml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Extract character_dict from PostProcess section
    char_dict = config.get('PostProcess', {}).get('character_dict', [])
    
    if not char_dict:
        raise ValueError("No character_dict found in YML config")
    
    # Write keys file (one character per line)
    with open(output_path, 'w', encoding='utf-8') as f:
        for char in char_dict:
            f.write(char + '\n')
    
    if on_progress:
        on_progress(f"Extracted {len(char_dict)} characters to {os.path.basename(output_path)}")
    
    return len(char_dict)

def download_models(on_progress=None):
    """Download PP-OCRv5 ONNX models from HuggingFace"""
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("Installing huggingface_hub...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])
        from huggingface_hub import hf_hub_download
    
    # Install PyYAML if needed
    try:
        import yaml
    except ImportError:
        print("Installing PyYAML...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
        import yaml
    
    models_dir = get_models_dir()
    os.makedirs(models_dir, exist_ok=True)
    
    # Download ONNX models from HuggingFace
    for name, filename in MODEL_FILES.items():
        target_path = os.path.join(models_dir, filename)
        if os.path.exists(target_path):
            if on_progress:
                on_progress(f"Model already exists: {filename}")
            continue
            
        if on_progress:
            on_progress(f"Downloading {filename}...")
        
        # Download to local dir
        downloaded_path = hf_hub_download(
            repo_id=HUGGINGFACE_REPO,
            filename=filename,
            local_dir=models_dir
        )
        
        if on_progress:
            on_progress(f"Downloaded: {filename}")
    
    # Download YML config and extract character dictionary
    keys_path = os.path.join(models_dir, REC_KEYS_FILE)
    if not os.path.exists(keys_path):
        if on_progress:
            on_progress(f"Downloading {REC_CONFIG_FILE}...")
        
        # Download YML config
        yml_path = hf_hub_download(
            repo_id=HUGGINGFACE_REPO,
            filename=REC_CONFIG_FILE,
            local_dir=models_dir
        )
        
        # Extract character dictionary from YML
        yml_full_path = os.path.join(models_dir, REC_CONFIG_FILE)
        extract_keys_from_yml(yml_full_path, keys_path, on_progress)
    else:
        if on_progress:
            on_progress(f"Character dictionary already exists: {REC_KEYS_FILE}")
    
    return True

def create_rapidocr_engine():
    """Create RapidOCR engine with PP-OCRv5 models"""
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        print("Installing rapidocr_onnxruntime...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rapidocr_onnxruntime"])
        from rapidocr_onnxruntime import RapidOCR
    
    models_dir = get_models_dir()
    
    det_model = os.path.join(models_dir, MODEL_FILES["det"])
    rec_model = os.path.join(models_dir, MODEL_FILES["rec"])
    rec_keys = os.path.join(models_dir, REC_KEYS_FILE)
    
    # Check if models exist
    if not os.path.exists(det_model):
        raise FileNotFoundError(f"Detection model not found: {det_model}")
    if not os.path.exists(rec_model):
        raise FileNotFoundError(f"Recognition model not found: {rec_model}")
    if not os.path.exists(rec_keys):
        raise FileNotFoundError(f"Character dictionary not found: {rec_keys}")
    
    # Create RapidOCR engine with custom models and character dictionary
    # Note: cls_model (text direction classifier) is disabled because PP-LCNet
    # expects different input dimensions than PP-OCRv5 produces
    engine = RapidOCR(
        det_model_path=det_model,
        rec_model_path=rec_model,
        cls_model_path=None,  # Disabled - incompatible with PP-OCRv5
        rec_keys_path=rec_keys
    )
    
    return engine

def process_image(engine, image, page_num=None):
    """Process a single image with RapidOCR and return Markdown text"""
    result, elapse = engine(image)
    
    if result is None:
        return ""
    
    # Build Markdown content from OCR results
    lines = []
    if page_num is not None:
        lines.append(f"## Page {page_num + 1}\n")
    
    for item in result:
        # item is (bbox, text, confidence)
        text = item[1]
        lines.append(text)
    
    return "\n".join(lines)

def convert_pdf(engine, input_path, output_path, on_progress=None):
    """Convert PDF to Markdown using RapidOCR"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("Installing PyMuPDF...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pymupdf"])
        import fitz
    
    import numpy as np
    
    doc = fitz.open(input_path)
    all_content = []
    
    for i, page in enumerate(doc):
        if on_progress:
            on_progress(f"Processing page {i+1}/{len(doc)}...")
        
        # Render page to image
        pix = page.get_pixmap(dpi=150)
        img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        
        # Convert to RGB if needed
        if pix.n == 4:
            import cv2
            img_data = cv2.cvtColor(img_data, cv2.COLOR_RGBA2RGB)
        elif pix.n == 1:
            import cv2
            img_data = cv2.cvtColor(img_data, cv2.COLOR_GRAY2RGB)
        
        # Process page
        page_content = process_image(engine, img_data, page_num=i)
        if page_content:
            all_content.append(page_content)
        
        print(f"Processed page {i+1}/{len(doc)}")
    
    doc.close()
    
    # Write output
    final_content = "\n\n---\n\n".join(all_content)
    
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    return True

def convert_image(engine, input_path, output_path, on_progress=None):
    """Convert image to Markdown using RapidOCR"""
    import cv2
    
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Failed to read image: {input_path}")
    
    if on_progress:
        on_progress("Processing image...")
    
    content = process_image(engine, img)
    
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    parser = argparse.ArgumentParser(description='RapidOCR PP-OCRv5 Conversion')
    parser.add_argument('input_file', nargs='?', help='Input file path (Image/PDF)')
    parser.add_argument('output_file', nargs='?', help='Output Markdown file path')
    parser.add_argument('--download-models', action='store_true', help='Download PP-OCRv5 models only')
    parser.add_argument('--check-models', action='store_true', help='Check if models are installed')
    
    args = parser.parse_args()
    
    # Check models command
    if args.check_models:
        if check_models_exist():
            print("MODELS_INSTALLED")
            sys.exit(0)
        else:
            print("MODELS_NOT_INSTALLED")
            sys.exit(1)
    
    # Download models command
    if args.download_models:
        print("Downloading PP-OCRv5 models...")
        try:
            download_models(on_progress=print)
            print("Models downloaded successfully.")
            sys.exit(0)
        except Exception as e:
            print(f"Error downloading models: {e}")
            traceback.print_exc()
            sys.exit(1)
    
    # Conversion mode
    if not args.input_file or not args.output_file:
        parser.print_help()
        sys.exit(1)
    
    input_path = os.path.abspath(args.input_file)
    output_path = os.path.abspath(args.output_file)
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        # Check and download models if needed
        if not check_models_exist():
            print("Models not found. Downloading...")
            download_models(on_progress=print)
        
        # Create engine
        print("Initializing RapidOCR with PP-OCRv5 models...")
        engine = create_rapidocr_engine()
        
        print(f"Starting conversion for: {input_path}")
        
        # Convert based on file type
        if input_path.lower().endswith('.pdf'):
            convert_pdf(engine, input_path, output_path, on_progress=print)
        else:
            convert_image(engine, input_path, output_path, on_progress=print)
        
        print(f"Conversion complete: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
