#!/usr/bin/env python3
"""Test generate_table_images option in Docling"""
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from pathlib import Path
import sys

input_pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Tests/Fixtures/ocr_mixed_test.pdf")
output_dir = Path("Tests/Output/docling_table_images_test")
output_dir.mkdir(parents=True, exist_ok=True)

print(f"Input: {input_pdf}")
print(f"Output: {output_dir}")

# Configure pipeline with table and picture image generation
pipeline_options = PdfPipelineOptions(
    generate_table_images=True,
    generate_picture_images=True,
)

print("\nPipeline options:")
print(f"  generate_table_images: {pipeline_options.generate_table_images}")
print(f"  generate_picture_images: {pipeline_options.generate_picture_images}")

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

print("\nConverting document...")
result = converter.convert(input_pdf)
doc = result.document

print(f"\nTables found: {len(doc.tables)}")
for i, table in enumerate(doc.tables):
    has_image = hasattr(table, 'image') and table.image is not None
    print(f"  Table {i}: has_image={has_image}")
    if has_image:
        img_path = output_dir / f"table_{i}.png"
        table.image.pil_image.save(img_path)
        print(f"    -> Saved: {img_path}")

print(f"\nPictures found: {len(doc.pictures)}")
for i, pic in enumerate(doc.pictures):
    has_image = hasattr(pic, 'image') and pic.image is not None
    print(f"  Picture {i}: has_image={has_image}")
    if has_image:
        img_path = output_dir / f"picture_{i}.png"
        pic.image.pil_image.save(img_path)
        print(f"    -> Saved: {img_path}")

# Export markdown
md_path = output_dir / "output.md"
md_content = doc.export_to_markdown()
md_path.write_text(md_content, encoding="utf-8")
print(f"\nMarkdown saved: {md_path}")

print("\nDone!")
