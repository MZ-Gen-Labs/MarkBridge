import os
import argparse
import sys
import json
import traceback

def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    finally:
        globals()[package] = importlib.import_module(package)

# Ensure required packages
try:
    import cv2
    import numpy as np
    from paddleocr import PPStructureV3 as PPStructure
    # from paddleocr.ppstructure.recovery.recovery_to_doc import sorted_layout_boxes # Removed due to import error
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    sys.exit(1)

def sorted_layout_boxes(res, w):
    """
    Sort text boxes by y-coordinate first, then x-coordinate.
    Simple implementation to replace the missing library function.
    """
    if len(res) == 0:
        return res
    return sorted(res, key=lambda x: (x['bbox'][1], x['bbox'][0]))



def convert_to_markdown(res, img_name):
    """
    Convert structure analysis result to Markdown.
    """
    if res is None: 
        return ""

    # Sort regions
    res = sorted_layout_boxes(res, w=0)

    md_lines = []

    for region in res:
        region_type = region['type']
        region_res = region.get('res', [])
        
        if region_type == 'table':
            if region_res and 'html' in region_res:
                 md_lines.append(region_res['html'])
                 md_lines.append("")
        
        elif region_type == 'figure':
            md_lines.append(f"![Figure]({img_name}_figure.jpg)") 
            
        elif region_type == 'text':
            text_block = ""
            for line in region_res:
                if isinstance(line, dict):
                    text_block += line.get('text', '') + " "
                elif isinstance(line, str):
                    text_block += line + " "
            md_lines.append(text_block.strip())
            md_lines.append("")
        
        elif region_type == 'title':
            text_block = ""
            for line in region_res:
                 if isinstance(line, dict):
                    text_block += line.get('text', '') + " "
            md_lines.append(f"## {text_block.strip()}")
            md_lines.append("")
            
        elif region_type == 'header':
             text_block = ""
             for line in region_res:
                 if isinstance(line, dict):
                    text_block += line.get('text', '') + " "
             md_lines.append(f"**{text_block.strip()}**")
             md_lines.append("")

    return "\n".join(md_lines)

def main():
    parser = argparse.ArgumentParser(description='PaddleOCR PP-Structure Conversion')
    parser.add_argument('input_file', help='Input file path (Image/PDF)')
    parser.add_argument('output_file', help='Output Markdown file path')
    parser.add_argument('--lang', default='japan', help='Language (japan, ch, en)')
    parser.add_argument('--use_gpu', action='store_true', help='Use GPU')
    
    args = parser.parse_args()
    
    input_path = args.input_file
    output_path = args.output_file
    lang = args.lang
    use_gpu = args.use_gpu

    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    try:
        # Initialize PaddleOCR engine
        print(f"Initializing PaddleOCR (lang={lang}, gpu={use_gpu})...")
        # PPStructureV3 might not support show_log or use_gpu in init directly in newer versions or wraps them differently.
        # Trying with minimal arguments first.
        # table_engine = PPStructure(show_log=True, lang=lang, use_gpu=use_gpu) 
        table_engine = PPStructure(lang=lang)

        print(f"Starting conversion for: {input_path}")
        
        # Check if input is PDF
        if input_path.lower().endswith('.pdf'):
            try:
                import fitz # PyMuPDF
                doc = fitz.open(input_path)
                all_md = []
                for i, page in enumerate(doc):
                    pix = page.get_pixmap()
                    img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                    if pix.n == 4:
                        img_data = cv2.cvtColor(img_data, cv2.COLOR_RGBA2RGB)
                    elif pix.n != 3:
                        img_data = cv2.cvtColor(img_data, cv2.COLOR_GRAY2RGB)
                    
                    result = table_engine(img_data)
                    page_md = convert_to_markdown(result, f"page_{i}")
                    all_md.append(page_md)
                    print(f"Processed page {i+1}/{len(doc)}")
                
                final_md = "\n\n---\n\n".join(all_md)
                
                output_dir = os.path.dirname(output_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(final_md)
                    
            except ImportError:
                 print("Error: PyMuPDF (fitz) not found. Please install it: pip install pymupdf")
                 sys.exit(1)
        else:
            # Image handling
            img = cv2.imread(input_path)
            if img is None:
                print("Error: Failed to read image using cv2")
                sys.exit(1)

            result = table_engine(img)
            md_content = convert_to_markdown(result, "img")
            
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

        print(f"Conversion complete: {output_path}")

    except Exception:
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
