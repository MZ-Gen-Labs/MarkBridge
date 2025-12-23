#!/usr/bin/env python3
"""
Docling Wrapper Script for MarkBridge Application
Converts PDF and other documents to Markdown using the docling library.
Supports OCR, image extraction, and GPU acceleration.
"""

import sys
import argparse
import re
from pathlib import Path
from urllib.parse import quote

def make_paths_relative(md_content: str, md_path: Path, images_dir: Path) -> str:
    """
    Convert absolute image paths to relative paths in markdown content.
    Also URL-encode spaces in path segments.
    """
    if not images_dir.exists():
        return md_content
    
    def replace_path(match):
        abs_path = match.group(1)
        try:
            abs_path_obj = Path(abs_path)
            if abs_path_obj.exists():
                # Calculate relative path from markdown file to image
                rel_path = abs_path_obj.relative_to(md_path.parent)
                # URL encode each path segment and use forward slashes
                parts = [quote(str(p)) for p in rel_path.parts]
                return f'![image]({"/".join(parts)})'
        except (ValueError, OSError):
            pass
        return match.group(0)
    
    # Match markdown image syntax with absolute paths
    pattern = r'!\[.*?\]\(([A-Za-z]:\\[^)]+)\)'
    return re.sub(pattern, replace_path, md_content)

def main():
    parser = argparse.ArgumentParser(description='Convert documents to Markdown using Docling')
    parser.add_argument('input_file', help='Input file to convert')
    parser.add_argument('--output', '-o', required=True, help='Output markdown file path')
    parser.add_argument('--ocr', action='store_true', help='Enable OCR for scanned documents')
    parser.add_argument('--export-images', action='store_true', help='Extract and save images')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu',
                        help='Device to use for inference (cpu or cuda)')
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.pipeline_options import PipelineOptions
        from docling.datamodel.base_models import InputFormat
        
        print(f"Processing: {input_path.name}")
        print(f"OCR: {'enabled' if args.ocr else 'disabled'}")
        print(f"Device: {args.device}")
        
        # Configure pipeline options
        pipeline_options = PipelineOptions()
        if args.ocr:
            pipeline_options.do_ocr = True
        
        # Create converter
        converter = DocumentConverter()
        
        # Convert document
        print("Converting document...")
        result = converter.convert(str(input_path))
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export to markdown
        md_content = result.document.export_to_markdown()
        
        # Handle image export
        images_dir = output_path.parent / f"{output_path.stem}_images"
        if args.export_images:
            print("Exporting images...")
            images_dir.mkdir(exist_ok=True)
            
            for i, image in enumerate(result.document.images):
                image_path = images_dir / f"image_{i+1}.png"
                image.save(str(image_path))
            
            # Convert absolute paths to relative
            md_content = make_paths_relative(md_content, output_path, images_dir)
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"Successfully converted: {input_path.name}")
        print(f"Output: {output_path}")
        if args.export_images and images_dir.exists():
            print(f"Images: {images_dir}")
        
    except ImportError as e:
        print(f"Error: Required package not installed. Run: pip install docling", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
