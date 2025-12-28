#!/usr/bin/env python3
"""Test custom markdown export with table images at correct positions"""
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling_core.types.doc import ImageRefMode, RefItem
from pathlib import Path
import re

input_pdf = Path('Tests/Fixtures/ocr_mixed_test.pdf')
output_dir = Path('Tests/Output/docling_custom_test')
output_dir.mkdir(parents=True, exist_ok=True)

p = PdfPipelineOptions(
    generate_table_images=True, 
    generate_picture_images=True,
    do_ocr=False
)
conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=p)})
result = conv.convert(input_pdf)
doc = result.document

# Save table images
table_images = {}
for i, table in enumerate(doc.tables):
    if hasattr(table, 'image') and table.image is not None:
        img_name = f"table_{i}.png"
        img_path = output_dir / img_name
        table.image.pil_image.save(img_path)
        table_images[f"#/tables/{i}"] = img_name
        print(f"Saved {img_name}")

# Generate markdown with custom table image insertion
md_lines = []
for item in doc.body.children:
    if isinstance(item, RefItem):
        ref = item.cref
        if ref.startswith('#/tables/'):
            # This is a table reference - insert image link
            if ref in table_images:
                img_name = table_images[ref]
                md_lines.append(f"\n![{img_name}]({img_name})\n")
        elif ref.startswith('#/texts/'):
            # This is a text reference - get the actual text
            # Need to resolve the reference
            try:
                idx = int(ref.split('/')[-1])
                if idx < len(doc.texts):
                    text_item = doc.texts[idx]
                    if hasattr(text_item, 'text'):
                        md_lines.append(text_item.text)
            except:
                pass
        # Handle other reference types as needed
        # groups, pictures, etc.
    else:
        # Non-reference item
        if hasattr(item, 'text'):
            md_lines.append(item.text)

# Write markdown
output_md = output_dir / "output.md"
with open(output_md, 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))

print(f"\nMarkdown saved to {output_md}")
print("\n--- Markdown content ---")
with open(output_md, 'r', encoding='utf-8') as f:
    content = f.read()
    print(content[:2000])
