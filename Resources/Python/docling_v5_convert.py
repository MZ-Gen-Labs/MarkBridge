#!/usr/bin/env python3
"""
Docling Conversion Script with PP-OCRv5 Models for MarkBridge
Uses Docling's document pipeline with RapidOCR engine configured to use PP-OCRv5 models.
This provides both the high-accuracy Japanese OCR of PP-OCRv5 AND Docling's structure recognition.
"""

import os
import sys
import argparse
import traceback
import uuid
import tempfile
import shutil
from pathlib import Path

# Model configuration
HUGGINGFACE_REPO = "marsena/paddleocr-onnx-models"
MODEL_FILES = {
    "det": "PP-OCRv5_server_det_infer.onnx",
    "rec": "PP-OCRv5_server_rec_infer.onnx",
}
REC_CONFIG_FILE = "PP-OCRv5_server_rec_infer.yml"
REC_KEYS_FILE = "pp_ocrv5_server_keys.txt"


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
    keys_path = os.path.join(models_dir, REC_KEYS_FILE)
    if not os.path.exists(keys_path):
        return False
    return True


def download_models_if_needed():
    """Download PP-OCRv5 models if not present"""
    if check_models_exist():
        return True
    
    print("Models not found. Downloading PP-OCRv5 models...")
    
    from huggingface_hub import hf_hub_download
    import yaml
    
    models_dir = get_models_dir()
    os.makedirs(models_dir, exist_ok=True)
    
    # Download ONNX models
    for name, filename in MODEL_FILES.items():
        target_path = os.path.join(models_dir, filename)
        if not os.path.exists(target_path):
            print(f"  Downloading {filename}...")
            hf_hub_download(
                repo_id=HUGGINGFACE_REPO,
                filename=filename,
                local_dir=models_dir
            )
    
    # Download and extract dictionary
    keys_path = os.path.join(models_dir, REC_KEYS_FILE)
    if not os.path.exists(keys_path):
        print(f"  Downloading {REC_CONFIG_FILE}...")
        hf_hub_download(
            repo_id=HUGGINGFACE_REPO,
            filename=REC_CONFIG_FILE,
            local_dir=models_dir
        )
        
        yml_path = os.path.join(models_dir, REC_CONFIG_FILE)
        print("  Extracting character dictionary...")
        with open(yml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        char_dict = config.get('PostProcess', {}).get('character_dict', [])
        with open(keys_path, 'w', encoding='utf-8') as f:
            for char in char_dict:
                f.write(char + '\n')
        print(f"  Extracted {len(char_dict)} characters")
    
    return True


def convert_document(input_path, output_path, use_gpu=False, force_ocr=False, image_mode="placeholder"):
    """Convert document using Docling with PP-OCRv5 models for OCR"""
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.datamodel.base_models import InputFormat
    from docling_core.types.doc import ImageRefMode
    
    try:
        from docling.datamodel.pipeline_options import RapidOcrOptions
    except ImportError:
        # Fallback for older versions
        from docling.datamodel.pipeline_options import OcrOptions as RapidOcrOptions
    
    # Get model paths
    models_dir = get_models_dir()
    det_model = os.path.join(models_dir, MODEL_FILES["det"])
    rec_model = os.path.join(models_dir, MODEL_FILES["rec"])
    rec_keys = os.path.join(models_dir, REC_KEYS_FILE)
    
    print(f"Using PP-OCRv5 models from: {models_dir}")
    
    # Configure RapidOCR with PP-OCRv5 models
    rapidocr_options = RapidOcrOptions(
        det_model_path=det_model,
        rec_model_path=rec_model,
        cls_model_path=None,  # Disabled - incompatible with PP-OCRv5
        rec_keys_path=rec_keys,
        force_full_page_ocr=force_ocr,  # Force OCR on all pages
    )
    
    # Configure PDF pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.ocr_options = rapidocr_options
    
    # Image export mode
    if image_mode == "embedded":
        pipeline_options.images_scale = 1.0
        pipeline_options.generate_picture_images = True
    
    # Configure format options
    pdf_options = PdfFormatOption(
        pipeline_options=pipeline_options,
    )
    
    # Create converter
    converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF, InputFormat.IMAGE, InputFormat.DOCX, InputFormat.HTML, InputFormat.PPTX],
        format_options={
            InputFormat.PDF: pdf_options,
        }
    )
    
    # Create unique temp directory to avoid conflicts when multiple engines process the same file
    temp_dir = tempfile.mkdtemp(prefix=f"docling_v5_{uuid.uuid4().hex[:8]}_")
    
    try:
        # Copy input file to temp directory to avoid conflicts
        input_filename = os.path.basename(input_path)
        temp_input_path = os.path.join(temp_dir, input_filename)
        shutil.copy2(input_path, temp_input_path)
        
        print(f"Converting: {input_path} (using temp: {temp_dir})")
        
        # Convert document from temp location
        result = converter.convert(temp_input_path)
        
        # Export to Markdown
        if image_mode == "embedded":
            markdown_content = result.document.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
        else:
            markdown_content = result.document.export_to_markdown()
        
        # Write output to final destination
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Conversion complete: {output_path}")
        return True
        
    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description='Docling conversion with PP-OCRv5')
    parser.add_argument('input_file', help='Input file path')
    parser.add_argument('output_file', help='Output Markdown file path')
    parser.add_argument('--gpu', action='store_true', help='Use GPU acceleration')
    parser.add_argument('--force-ocr', action='store_true', help='Force OCR on all pages')
    parser.add_argument('--image-mode', choices=['placeholder', 'embedded', 'referenced'], 
                       default='placeholder', help='Image export mode')
    parser.add_argument('--download-models', action='store_true', help='Download models only')
    
    args = parser.parse_args()
    
    # Download models only mode
    if args.download_models:
        try:
            download_models_if_needed()
            print("Models ready.")
            sys.exit(0)
        except Exception as e:
            print(f"Error downloading models: {e}")
            traceback.print_exc()
            sys.exit(1)
    
    # Check input file
    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)
    
    try:
        # Ensure models are available
        download_models_if_needed()
        
        # Convert
        convert_document(
            args.input_file,
            args.output_file,
            use_gpu=args.gpu,
            force_ocr=args.force_ocr,
            image_mode=args.image_mode
        )
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
