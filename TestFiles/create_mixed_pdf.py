"""
OCRテスト用 - テキストと画像が混在するPDF
テキスト部分は選択可能、表は画像として埋め込み（OCR必要）
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image, ImageDraw, ImageFont
import os

# Register Japanese font
try:
    pdfmetrics.registerFont(TTFont('Meiryo', 'C:/Windows/Fonts/meiryo.ttc'))
    FONT_NAME = 'Meiryo'
except:
    FONT_NAME = 'Helvetica'

def create_table_image(data, filename, col_widths=None):
    """表を画像として生成"""
    cell_height = 40
    padding = 10
    font_size = 18
    
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", font_size)
        header_font = ImageFont.truetype("C:/Windows/Fonts/meiryob.ttc", font_size)
    except:
        font = ImageFont.load_default()
        header_font = font
    
    if col_widths is None:
        col_widths = [150] * len(data[0])
    total_width = sum(col_widths) + padding * 2
    total_height = len(data) * cell_height + padding * 2
    
    img = Image.new('RGB', (total_width, total_height), 'white')
    draw = ImageDraw.Draw(img)
    
    y = padding
    for row_idx, row in enumerate(data):
        x = padding
        for col_idx, cell in enumerate(row):
            draw.rectangle([x, y, x + col_widths[col_idx], y + cell_height], 
                          outline='black', width=2)
            
            if row_idx == 0:
                draw.rectangle([x+2, y+2, x + col_widths[col_idx]-2, y + cell_height-2], 
                              fill='#4472C4')
                text_color = 'white'
                use_font = header_font
            else:
                if row_idx % 2 == 0:
                    draw.rectangle([x+2, y+2, x + col_widths[col_idx]-2, y + cell_height-2], 
                                  fill='#E8F0FE')
                text_color = 'black'
                use_font = font
            
            text_bbox = draw.textbbox((0, 0), str(cell), font=use_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = x + (col_widths[col_idx] - text_width) // 2
            text_y = y + (cell_height - text_height) // 2
            draw.text((text_x, text_y), str(cell), fill=text_color, font=use_font)
            
            x += col_widths[col_idx]
        y += cell_height
    
    img.save(filename)
    return filename

def create_mixed_pdf():
    output_dir = 'c:/git/MarkBridge/TestFiles'
    pdf_path = os.path.join(output_dir, 'ocr_mixed_test.pdf')
    
    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                  fontName=FONT_NAME, fontSize=20, spaceAfter=20)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                    fontName=FONT_NAME, fontSize=14, 
                                    spaceBefore=20, spaceAfter=10)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'],
                                   fontName=FONT_NAME, fontSize=11, spaceAfter=10)
    caption_style = ParagraphStyle('Caption', parent=styles['Normal'],
                                    fontName=FONT_NAME, fontSize=9, 
                                    textColor='gray', spaceAfter=15)
    
    story = []
    
    # Title (TEXT - selectable)
    story.append(Paragraph("OCRテスト用ドキュメント（混在形式）", title_style))
    story.append(Paragraph("このPDFはテキストと画像が混在しています。", normal_style))
    story.append(Paragraph("テキスト部分は選択可能ですが、表は画像として埋め込まれており、OCR処理が必要です。", normal_style))
    story.append(Spacer(1, 20))
    
    # Section 1 (TEXT)
    story.append(Paragraph("1. 製品カタログ", heading_style))
    story.append(Paragraph("以下の表は当社の主要製品一覧です。価格は税込み表示となっています。", normal_style))
    
    # Table 1 (IMAGE - requires OCR)
    table1_data = [
        ['製品名', '説明', '単価', '在庫'],
        ['製品A-100', '高性能モデル', '¥12,800', '150'],
        ['製品B-200', 'スタンダード', '¥8,500', '320'],
        ['製品C-300', 'エコノミー', '¥4,200', '500'],
        ['製品D-400', 'プレミアム', '¥25,000', '50'],
    ]
    table1_img = create_table_image(table1_data, 
                                     os.path.join(output_dir, 'mixed_table1.png'),
                                     col_widths=[140, 160, 100, 80])
    story.append(RLImage(table1_img, width=13*cm, height=5.5*cm))
    story.append(Paragraph("図1: 製品カタログ一覧（画像）", caption_style))
    
    # Section 2 (TEXT)
    story.append(Paragraph("2. 四半期売上レポート", heading_style))
    story.append(Paragraph("2024年度の四半期別売上データを以下に示します。前年同期比で15%の成長を達成しました。", normal_style))
    
    # Table 2 (IMAGE - requires OCR)
    table2_data = [
        ['期間', '売上高', '利益', '成長率'],
        ['2024 Q1', '¥45,200,000', '¥8,540,000', '+12%'],
        ['2024 Q2', '¥52,800,000', '¥10,120,000', '+18%'],
        ['2024 Q3', '¥48,600,000', '¥9,230,000', '+15%'],
        ['2024 Q4', '¥61,400,000', '¥12,800,000', '+22%'],
    ]
    table2_img = create_table_image(table2_data,
                                     os.path.join(output_dir, 'mixed_table2.png'),
                                     col_widths=[100, 140, 120, 80])
    story.append(RLImage(table2_img, width=12*cm, height=5.5*cm))
    story.append(Paragraph("図2: 四半期売上データ（画像）", caption_style))
    
    # Section 3 (TEXT)
    story.append(Paragraph("3. 注意事項", heading_style))
    story.append(Paragraph("• 上記の表は画像として埋め込まれているため、テキスト選択ができません。", normal_style))
    story.append(Paragraph("• DoclingのOCR機能を使用すると、これらの表からテキストを抽出できます。", normal_style))
    story.append(Paragraph("• 表構造認識（TableFormer）により、Markdownテーブルとして出力されます。", normal_style))
    story.append(Spacer(1, 15))
    
    # Section 4 (TEXT)
    story.append(Paragraph("4. まとめ", heading_style))
    story.append(Paragraph("このテストドキュメントは、OCR機能のテストに最適です。画像として埋め込まれた表がMarkdown形式に正しく変換されるかを確認してください。", normal_style))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("―― テストドキュメント終了 ――", normal_style))
    
    doc.build(story)
    
    print(f"Mixed PDF created: {pdf_path}")
    print("- Text sections: Selectable (no OCR needed)")
    print("- Table images: Require OCR for text extraction")

if __name__ == "__main__":
    create_mixed_pdf()
