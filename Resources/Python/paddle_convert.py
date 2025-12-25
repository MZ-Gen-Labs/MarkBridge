
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


# Add nvidia dll paths for Windows if possible and pre-load them
if os.name == 'nt':
    import glob
    site_packages = os.path.join(sys.prefix, 'Lib', 'site-packages')
    nvidia_path = os.path.join(site_packages, 'nvidia')
    
    dll_paths_to_add = []
    
    if os.path.exists(nvidia_path):
        for dll_dir in glob.glob(os.path.join(nvidia_path, '*', 'bin')):
            dll_paths_to_add.append(dll_dir)
    
    # Add torch lib path (for zlibwapi.dll which might be there)
    torch_path = os.path.join(site_packages, 'torch', 'lib')
    if os.path.exists(torch_path):
         dll_paths_to_add.append(torch_path)

    # Add directories
    for p in dll_paths_to_add:
        print(f"DEBUG: Adding DLL directory: {p}")
        try:
             os.add_dll_directory(p)
        except Exception as e:
             print(f"DEBUG: Failed to add dll dir {p}: {e}")
        os.environ['PATH'] = p + os.pathsep + os.environ['PATH']

import paddle






def main():
    parser = argparse.ArgumentParser(description='PaddleOCR PP-Structure Conversion')
    parser.add_argument('input_file', help='Input file path (Image/PDF)')
    parser.add_argument('output_file', help='Output Markdown file path')
    parser.add_argument('--lang', default='japan', help='Language (japan, ch, en)')
    parser.add_argument('--use_gpu', action='store_true', help='Use GPU')
    
    args = parser.parse_args()
    
    input_path = os.path.abspath(args.input_file)
    output_path = os.path.abspath(args.output_file)
    lang = args.lang
    use_gpu = args.use_gpu

    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    try:
        # Initialize PaddleOCR engine
        print(f"Initializing PaddleOCR (lang={lang}, gpu={use_gpu})...")
        device = 'gpu' if use_gpu else 'cpu'
        
        try:
             table_engine = PPStructure(lang=lang, device=device)
        except Exception as e:
             if device == 'gpu':
                 print(f"Warning: Failed to initialize PaddleOCR with GPU: {e}")
                 print("Falling back to CPU...")
                 table_engine = PPStructure(lang=lang, device='cpu')
             else:
                 raise e

        print(f"Starting conversion for: {input_path}")
        
        # Temp dir for intermediate results
        import tempfile
        import shutil
        import uuid
        
        temp_base_dir = os.path.join(os.path.dirname(output_path), "paddle_temp_" + str(uuid.uuid4())[:8])
        if not os.path.exists(temp_base_dir):
            os.makedirs(temp_base_dir)

        all_md_content = []

        try:
            # Check if input is PDF
            if input_path.lower().endswith('.pdf'):
                try:
                    import fitz # PyMuPDF
                    doc = fitz.open(input_path)
                    
                    for i, page in enumerate(doc):
                        pix = page.get_pixmap()
                        img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                        if pix.n == 4:
                             img_data = cv2.cvtColor(img_data, cv2.COLOR_RGBA2RGB)
                        elif pix.n != 3:
                             img_data = cv2.cvtColor(img_data, cv2.COLOR_GRAY2RGB)
                        
                        # Process page
                        # predict returns a generator or list
                        results = table_engine.predict(img_data)
                        
                        # results might be a list of one item or a generator
                        # Iterate to handle both
                        if not isinstance(results, list):
                             results = [results] if not hasattr(results, '__iter__') else list(results)

                        for res_idx, res in enumerate(results):
                             # Each res corresponds to an image (here 1 image)
                             # Use save_to_markdown
                             page_temp_dir = os.path.join(temp_base_dir, f"page_{i}_{res_idx}")
                             if hasattr(res, 'save_to_markdown'):
                                 res.save_to_markdown(save_path=page_temp_dir)
                             else:
                                 # Fallback for older versions or unexpected objects?
                                 # Current V3 objects should have it.
                                 print(f"Warning: Result object missing save_to_markdown")
                                 continue
                             
                             # Find the generated MD file
                             md_files = [f for f in os.listdir(page_temp_dir) if f.endswith('.md')]
                             if md_files:
                                 with open(os.path.join(page_temp_dir, md_files[0]), 'r', encoding='utf-8') as f:
                                     all_md_content.append(f.read())
                             else:
                                 # It might output nothing if empty?
                                 pass
                        
                        print(f"Processed page {i+1}/{len(doc)}")
                        
                except ImportError:
                     print("Error: PyMuPDF (fitz) not found. Please install it: pip install pymupdf")
                     sys.exit(1)
            else:
                # Image handling
                img = cv2.imread(input_path)
                if img is None:
                    print("Error: Failed to read image using cv2")
                    sys.exit(1)

                results = table_engine.predict(img)
                # results is likely a generator yielding one result
                for res in results:
                     if hasattr(res, 'save_to_markdown'):
                         res.save_to_markdown(save_path=temp_base_dir)
                         # Find MD
                         md_files = [f for f in os.listdir(temp_base_dir) if f.endswith('.md')]
                         if md_files:
                              with open(os.path.join(temp_base_dir, md_files[0]), 'r', encoding='utf-8') as f:
                                   all_md_content.append(f.read())

            # Write final output
            final_md = "\n\n---\n\n".join(all_md_content)
            
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_md)

            print(f"Conversion complete: {output_path}")

        finally:
            # Cleanup temp
            if os.path.exists(temp_base_dir):
                try:
                    shutil.rmtree(temp_base_dir)
                except:
                    pass

    except Exception:
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

