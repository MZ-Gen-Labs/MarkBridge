"""
Marker PDF Converter Script for MarkBridge
Converts PDF files to Markdown using Marker library.

Usage:
    python marker_convert.py <input_file> <output_dir> [options]

Options:
    --use-gpu          Use GPU for processing
    --language LANG    Document language (default: auto)
    --use-llm          Use LLM for enhanced accuracy (requires API key)
"""

import argparse
import os
import sys
import json
from pathlib import Path


def convert_with_marker(
    input_path: str,
    output_dir: str,
    use_gpu: bool = False,
    language: str = None,
    use_llm: bool = False
) -> dict:
    """
    Convert a document to Markdown using Marker.
    
    Args:
        input_path: Path to input PDF file
        output_dir: Directory to save output files
        use_gpu: Whether to use GPU acceleration
        language: Document language (optional)
        use_llm: Whether to use LLM enhancement
        
    Returns:
        dict with conversion result information
    """
    try:
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.output import text_from_rendered
    except ImportError as e:
        return {
            "success": False,
            "error": f"Marker not installed: {e}",
            "output_path": None
        }
    
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Create model configuration
        config_dict = {}
        
        if use_gpu:
            config_dict["device"] = "cuda"
        else:
            config_dict["device"] = "cpu"
            
        if language:
            config_dict["languages"] = [language]
            
        # Create converter
        converter = PdfConverter(
            artifact_dict=create_model_dict(),
            config=config_dict
        )
        
        # Convert document
        rendered = converter(input_path)
        
        # Get text and images
        text, images, out_metadata = text_from_rendered(rendered)
        
        # Determine output filename
        input_name = Path(input_path).stem
        output_md_path = os.path.join(output_dir, f"{input_name}.md")
        
        # Save markdown
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        # Save images
        images_saved = []
        if images:
            images_dir = os.path.join(output_dir, f"{input_name}_images")
            os.makedirs(images_dir, exist_ok=True)
            
            for img_name, img_data in images.items():
                img_path = os.path.join(images_dir, img_name)
                # img_data is a PIL Image
                img_data.save(img_path)
                images_saved.append(img_path)
        
        return {
            "success": True,
            "output_path": output_md_path,
            "images_count": len(images_saved),
            "images_dir": images_dir if images_saved else None,
            "metadata": out_metadata
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "output_path": None
        }


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF to Markdown using Marker"
    )
    parser.add_argument("input_file", help="Input PDF file path")
    parser.add_argument("output_dir", help="Output directory path")
    parser.add_argument("--use-gpu", action="store_true", help="Use GPU acceleration")
    parser.add_argument("--language", type=str, default=None, help="Document language")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM enhancement")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.isfile(args.input_file):
        result = {
            "success": False,
            "error": f"Input file not found: {args.input_file}",
            "output_path": None
        }
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    
    # Run conversion
    result = convert_with_marker(
        input_path=args.input_file,
        output_dir=args.output_dir,
        use_gpu=args.use_gpu,
        language=args.language,
        use_llm=args.use_llm
    )
    
    # Output result
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        if result["success"]:
            print(f"Conversion successful!")
            print(f"Output: {result['output_path']}")
            if result.get("images_count", 0) > 0:
                print(f"Images: {result['images_count']} (in {result['images_dir']})")
        else:
            print(f"Conversion failed: {result['error']}", file=sys.stderr)
    
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
