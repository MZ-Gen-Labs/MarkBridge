#!/usr/bin/env python3
"""Investigate Docling document structure for table reference positions"""
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling_core.types.doc import ImageRefMode
from pathlib import Path

p = PdfPipelineOptions(generate_table_images=True, generate_picture_images=True)
conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=p)})
result = conv.convert(Path('Tests/Fixtures/ocr_mixed_test.pdf'))
doc = result.document

print('=== Tables Info ===')
for i, table in enumerate(doc.tables):
    print(f'Table {i}: self_ref = {table.self_ref}')

print('\n=== Document Body Children ===')
for i, item in enumerate(doc.body.children):
    item_type = type(item).__name__
    item_ref = getattr(item, 'ref', None) or getattr(item, 'cref', None) or getattr(item, '$ref', None)
    
    if item_type == 'RefItem':
        # Get the reference target
        ref_target = getattr(item, 'cref', None) or str(item)
        print(f'{i}: {item_type} -> {ref_target}')
    elif hasattr(item, 'text'):
        text_preview = item.text[:60].replace('\n', ' ') if len(item.text) > 60 else item.text.replace('\n', ' ')
        print(f'{i}: {item_type} - "{text_preview}"')
    else:
        print(f'{i}: {item_type} - {str(item)[:80]}')

print('\n=== Export to Markdown (showing structure) ===')
# Check where tables appear in the markdown
md = doc.export_to_markdown()
lines = md.split('\n')
for i, line in enumerate(lines):
    if '|' in line or 'table' in line.lower() or line.strip().startswith('#'):
        print(f'{i}: {line[:80]}')
