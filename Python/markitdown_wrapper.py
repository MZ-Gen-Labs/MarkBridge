#!/usr/bin/env python3
"""
MarkItDown Wrapper Script for MarkBridge Application
Converts various file formats to Markdown using the markitdown library.
"""

import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Convert files to Markdown using MarkItDown')
    parser.add_argument('input_file', help='Input file to convert')
    parser.add_argument('-o', '--output', required=True, help='Output markdown file path')
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        from markitdown import MarkItDown
        
        md = MarkItDown()
        result = md.convert(str(input_path))
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.text_content)
        
        print(f"Successfully converted: {input_path.name}")
        print(f"Output: {output_path}")
        
    except ImportError:
        print("Error: markitdown package not installed. Run: pip install markitdown", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
