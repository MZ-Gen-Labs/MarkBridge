#!/usr/bin/env python3
"""Test: Find markdown table blocks and insert image links after them"""
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling_core.types.doc import ImageRefMode
from pathlib import Path
import re

input_pdf = Path('Tests/Fixtures/ocr_mixed_test.pdf')
output_dir = Path('Tests/Output/docling_table_insert_test')
output_dir.mkdir(parents=True, exist_ok=True)

# Use OCR to get table content in markdown, then add images
p = PdfPipelineOptions(
    generate_table_images=True, 
    generate_picture_images=True,
    do_ocr=True  # Enable OCR to get table content
)
conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=p)})
result = conv.convert(input_pdf)
doc = result.document

print(f"Found {len(doc.tables)} tables")

# Save table images
table_images = []
for i, table in enumerate(doc.tables):
    if hasattr(table, 'image') and table.image is not None:
        img_name = f"table_{i}.png"
        img_path = output_dir / img_name
        table.image.pil_image.save(img_path)
        table_images.append(img_name)
        print(f"Saved {img_name}")

# Get markdown content
md_content = doc.export_to_markdown()

# Find markdown table blocks and insert image links after each
# A markdown table is a group of lines starting with |
lines = md_content.split('\n')
new_lines = []
table_index = 0
in_table = False

for i, line in enumerate(lines):
    current_is_table = line.strip().startswith('|')
    
    if current_is_table:
        in_table = True
        new_lines.append(line)
    else:
        if in_table:
            # Was in table, now exiting - insert image link
            if table_index < len(table_images):
                img_name = table_images[table_index]
                new_lines.append(f"\n![Table {table_index + 1}]({img_name})")
                table_index += 1
            in_table = False
        new_lines.append(line)

# Handle case where document ends with a table
if in_table and table_index < len(table_images):
    img_name = table_images[table_index]
    new_lines.append(f"\n![Table {table_index + 1}]({img_name})")

# Write result
output_md = output_dir / "output.md"
with open(output_md, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f"\nOutput saved to {output_md}")
print(f"Inserted {min(table_index + (1 if in_table else 0), len(table_images))} table image links")

# Show where images are in the output
print("\n--- Lines with image links ---")
with open(output_md, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '![' in line:
            print(f"Line {i+1}: {line.strip()}")
