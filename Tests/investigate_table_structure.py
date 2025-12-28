#!/usr/bin/env python3
"""Investigate Docling table structure for position information"""
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from pathlib import Path

p = PdfPipelineOptions(generate_table_images=True, generate_picture_images=True)
conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=p)})
result = conv.convert(Path('Tests/Fixtures/ocr_mixed_test.pdf'))
doc = result.document

print('=== Document Tables ===')
for i, table in enumerate(doc.tables):
    print(f'\nTable {i}:')
    if hasattr(table, 'label'):
        print(f'  Label: {table.label}')
    if hasattr(table, 'self_ref'):
        print(f'  Self ref: {table.self_ref}')
    if hasattr(table, 'prov') and table.prov:
        for p in table.prov:
            print(f'  Page: {getattr(p, "page_no", "?")}')
            if hasattr(p, 'bbox'):
                print(f'  BBox: {p.bbox}')

print('\n=== Document Body Structure ===')
for i, item in enumerate(doc.body.children[:20]):  # First 20 items
    item_type = type(item).__name__
    if hasattr(item, 'label'):
        print(f'{i}: {item_type} - label={item.label}')
    elif hasattr(item, 'text'):
        text_preview = item.text[:50] if len(item.text) > 50 else item.text
        print(f'{i}: {item_type} - text="{text_preview}"')
    else:
        print(f'{i}: {item_type}')
