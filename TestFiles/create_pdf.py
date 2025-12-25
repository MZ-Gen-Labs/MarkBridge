"""
OCRテスト用PDFを生成するスクリプト
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Register Japanese font
try:
    pdfmetrics.registerFont(TTFont('Meiryo', 'C:/Windows/Fonts/meiryo.ttc'))
    FONT_NAME = 'Meiryo'
except:
    FONT_NAME = 'Helvetica'

def create_test_pdf():
    output_path = 'c:/git/MarkBridge/TestFiles/ocr_test.pdf'
    doc = SimpleDocTemplate(output_path, pagesize=A4, 
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=18,
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10,
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        spaceAfter=8,
    )
    
    story = []
    
    # Title
    story.append(Paragraph("OCRテスト用ドキュメント", title_style))
    story.append(Paragraph("作成日: 2024年12月25日", normal_style))
    story.append(Spacer(1, 20))
    
    # Text section
    story.append(Paragraph("1. テキスト認識テスト", heading_style))
    story.append(Paragraph("日本語テキスト: これは日本語の文章です。漢字、ひらがな、カタカナが含まれています。", normal_style))
    story.append(Paragraph("English Text: This is an English sentence for OCR testing purposes.", normal_style))
    story.append(Spacer(1, 15))
    
    # Table section
    story.append(Paragraph("2. 表（テーブル）認識テスト", heading_style))
    
    # Simple table
    story.append(Paragraph("基本的な表:", normal_style))
    table_data = [
        ['項目', '説明', '価格'],
        ['商品A', '高品質な製品', '¥1,200'],
        ['商品B', 'スタンダード製品', '¥800'],
        ['商品C', 'エコノミー製品', '¥500'],
    ]
    table = Table(table_data, colWidths=[4*cm, 6*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(table)
    story.append(Spacer(1, 15))
    
    # Complex table with numbers
    story.append(Paragraph("複雑な表（数値データ）:", normal_style))
    number_data = [
        ['年度', 'Q1', 'Q2', 'Q3', 'Q4', '合計'],
        ['2022', '1,234', '2,345', '3,456', '4,567', '11,602'],
        ['2023', '1,500', '2,800', '3,200', '5,100', '12,600'],
        ['2024', '1,800', '3,100', '4,200', '5,500', '14,600'],
    ]
    table2 = Table(number_data, colWidths=[2.5*cm]*6)
    table2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(table2)
    story.append(Spacer(1, 15))
    
    # List section
    story.append(Paragraph("3. リスト認識テスト", heading_style))
    story.append(Paragraph("• 項目1: 最初の項目", normal_style))
    story.append(Paragraph("• 項目2: 2番目の項目", normal_style))
    story.append(Paragraph("• 項目3: 3番目の項目", normal_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("1. 手順1: 準備をする", normal_style))
    story.append(Paragraph("2. 手順2: 実行する", normal_style))
    story.append(Paragraph("3. 手順3: 確認する", normal_style))
    story.append(Spacer(1, 15))
    
    # Code section
    story.append(Paragraph("4. コードブロック認識テスト", heading_style))
    code_text = """def hello_world():
    print("Hello, World!")
    return True

for i in range(10):
    print(i)"""
    code_style = ParagraphStyle('Code', fontName='Courier', fontSize=9, backColor=colors.lightgrey)
    story.append(Preformatted(code_text, code_style))
    story.append(Spacer(1, 15))
    
    # Formula section
    story.append(Paragraph("5. 数式認識テスト", heading_style))
    story.append(Paragraph("E = mc²", normal_style))
    story.append(Paragraph("∑(i=1 to n) xi = x1 + x2 + ... + xn", normal_style))
    story.append(Spacer(1, 15))
    
    # Comparison table
    story.append(Paragraph("6. エンジン比較表", heading_style))
    comp_data = [
        ['エンジン', 'OCR', '表認識', '速度'],
        ['MarkItDown', '×', '△', '◎'],
        ['Docling (CPU)', '○', '◎', '○'],
        ['Docling (GPU)', '○', '◎', '◎'],
    ]
    table3 = Table(comp_data, colWidths=[4*cm, 2*cm, 2*cm, 2*cm])
    table3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(table3)
    
    story.append(Spacer(1, 30))
    story.append(Paragraph("テストドキュメント終了", normal_style))
    
    doc.build(story)
    print(f"PDF created: {output_path}")

if __name__ == "__main__":
    create_test_pdf()
