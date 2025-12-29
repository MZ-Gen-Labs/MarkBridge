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


def convert_document(input_path, output_path, use_gpu=False, force_ocr=False, enable_ocr=True, image_mode="placeholder"):
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
    pipeline_options.do_ocr = enable_ocr  # Control OCR via parameter
    if enable_ocr:
        pipeline_options.ocr_options = rapidocr_options
    else:
        # When OCR is disabled, also disable table structure detection
        # This allows tables to be treated as images
        pipeline_options.do_table_structure = False
    
    # Image export mode
    if image_mode in ("embedded", "referenced"):
        pipeline_options.images_scale = 1.0
        pipeline_options.generate_picture_images = True
        pipeline_options.generate_page_images = True  # Also generate page images
        pipeline_options.generate_table_images = True  # Generate table images for export
    
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
        
        print(f"  Detected: {len(result.document.pictures)} pictures, {len(result.document.tables)} tables")
        
        # Prepare output directory
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Export to Markdown based on image mode
        # Use save_as_markdown for REFERENCED mode (automatically saves images as files)
        # Use export_to_markdown for EMBEDDED mode (returns markdown string with base64 images)
        from pathlib import Path
        
        if image_mode == "embedded":
            # Embedded mode: use export_to_markdown and write manually
            markdown_content = result.document.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        elif image_mode == "referenced":
            # Referenced mode: use save_as_markdown which automatically saves images
            result.document.save_as_markdown(Path(output_path), image_mode=ImageRefMode.REFERENCED)
            print(f"  Images saved alongside markdown file")
            
            # Create images folder based on output filename (e.g., test.md -> test/)
            output_basename = Path(output_path).stem
            output_dir_path = Path(output_dir) if output_dir else Path(".")
            images_folder = output_dir_path / output_basename
            images_folder.mkdir(parents=True, exist_ok=True)
            
            # Save table images to the basename folder
            tables_saved = []
            for i, table in enumerate(result.document.tables):
                if hasattr(table, 'image') and table.image is not None:
                    table_img_name = f"table_{i}.png"
                    table_img_path = images_folder / table_img_name
                    table.image.pil_image.save(table_img_path)
                    # Store relative path from markdown file location
                    tables_saved.append(f"{output_basename}/{table_img_name}")
            
            if tables_saved:
                print(f"  Saved {len(tables_saved)} table images to {images_folder}")
                
                # Insert table image links into markdown file
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Strategy: Find table position in document body and match with markdown
                # Get text items that come after each table
                from docling_core.types.doc import RefItem
                
                table_contexts = {}  # table_ref -> text that follows
                # We need to access the body children. 
                # result.document.body.children is an iterator/list of Items
                body_children = list(result.document.body.children)
                
                for idx, item in enumerate(body_children):
                    if isinstance(item, RefItem) and str(item.cref).startswith('#/tables/'):
                        table_ref = str(item.cref)
                        # Get the next text item after this table
                        for next_idx in range(idx + 1, min(idx + 5, len(body_children))):
                            next_item = body_children[next_idx]
                            if isinstance(next_item, RefItem):
                                next_ref = str(next_item.cref)
                                if next_ref.startswith('#/texts/'):
                                    try:
                                        text_idx = int(next_ref.split('/')[-1])
                                        if text_idx < len(result.document.texts):
                                            text_item = result.document.texts[text_idx]
                                            if hasattr(text_item, 'text') and text_item.text:
                                                # Use first 30 chars as marker
                                                marker = text_item.text[:30].strip()
                                                if marker:
                                                    table_contexts[table_ref] = marker
                                                    break
                                    except (ValueError, IndexError):
                                        pass
                
                # Insert image links before the text that follows each table
                lines = content.split('\n')
                new_content = content
                
                # tables_saved list in this script is just filenames, we need to re-associate with refs
                # We iterate tables again to map index to ref
                table_refs_map = {}
                for i, table in enumerate(result.document.tables):
                     if hasattr(table, 'image') and table.image is not None and i < len(tables_saved):
                         table_refs_map[i] = table.self_ref

                inserted_indices = set()
                
                for i, img_name in enumerate(tables_saved):
                    table_ref = table_refs_map.get(i)
                    if table_ref and table_ref in table_contexts:
                        marker = table_contexts[table_ref]
                        # Find the marker in content and insert image before it
                        import re
                        # Escape special regex characters
                        escaped_marker = re.escape(marker)
                        pattern = f"({escaped_marker})"
                        replacement = f"![Table {i + 1}]({img_name})\n\n\\1"
                        new_content, count = re.subn(pattern, replacement, new_content, count=1)
                        if count > 0:
                            inserted_indices.add(i)
                    else:
                        # Fallback: check if markdown table exists (for OCR enabled case)
                        pass
                
                # Strategy 2: If no context found (or fallback needed), check for markdown table blocks
                # This handles cases where OCR is enabled and table is rendered as markdown table
                if len(inserted_indices) < len(tables_saved):
                    lines = new_content.split('\n')
                    new_lines_strategy2 = []
                    table_index = 0
                    in_table = False
                    
                    for line in lines:
                        new_lines_strategy2.append(line)
                        if line.strip().startswith('|'):
                            in_table = True
                        elif in_table:
                            in_table = False
                            # Try to insert next available table
                            while table_index < len(tables_saved) and table_index in inserted_indices:
                                table_index += 1
                                
                            if table_index < len(tables_saved):
                                img_name = tables_saved[table_index]
                                new_lines_strategy2.append(f"\n![Table {table_index + 1}]({img_name})")
                                inserted_indices.add(table_index)
                                table_index += 1

                    if in_table: # End of doc table
                        while table_index < len(tables_saved) and table_index in inserted_indices:
                            table_index += 1
                        if table_index < len(tables_saved):
                             img_name = tables_saved[table_index]
                             new_lines_strategy2.append(f"\n![Table {table_index + 1}]({img_name})")
                             inserted_indices.add(table_index)

                    new_content = '\n'.join(new_lines_strategy2)

                # Strategy 3: Append remaining at end
                remaining_indices = [i for i in range(len(tables_saved)) if i not in inserted_indices]
                if remaining_indices:
                    new_content += "\n\n## Table Images\n"
                    for i in remaining_indices:
                         img_name = tables_saved[i]
                         new_content += f"\n![Table {i + 1}]({img_name})"

                # Write updated content
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"  Inserted {len(tables_saved)} table image links")
        else:
            # Placeholder mode: no images
            markdown_content = result.document.export_to_markdown()
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
    parser.add_argument('--no-ocr', action='store_true', help='Disable OCR')
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
            enable_ocr=not args.no_ocr,
            image_mode=args.image_mode
        )
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
