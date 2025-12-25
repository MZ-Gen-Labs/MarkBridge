"""
OCRテスト用 - 画像ベースのPDFを生成（スキャンドキュメントをシミュレート）
表やテキストを画像としてレンダリングしてPDFに埋め込む
"""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from PIL import Image, ImageDraw, ImageFont
import os

def create_table_image(data, filename, col_widths=None):
    """表を画像として生成"""
    # Settings
    cell_height = 40
    padding = 10
    font_size = 20
    
    # Try to use Japanese font
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", font_size)
        header_font = ImageFont.truetype("C:/Windows/Fonts/meiryob.ttc", font_size)
    except:
        font = ImageFont.load_default()
        header_font = font
    
    # Calculate dimensions
    if col_widths is None:
        col_widths = [150] * len(data[0])
    total_width = sum(col_widths) + padding * 2
    total_height = len(data) * cell_height + padding * 2
    
    # Create image
    img = Image.new('RGB', (total_width, total_height), 'white')
    draw = ImageDraw.Draw(img)
    
    y = padding
    for row_idx, row in enumerate(data):
        x = padding
        for col_idx, cell in enumerate(row):
            # Draw cell border
            draw.rectangle([x, y, x + col_widths[col_idx], y + cell_height], 
                          outline='black', width=2)
            
            # Header row background
            if row_idx == 0:
                draw.rectangle([x+2, y+2, x + col_widths[col_idx]-2, y + cell_height-2], 
                              fill='#4472C4')
                text_color = 'white'
                use_font = header_font
            else:
                text_color = 'black'
                use_font = font
            
            # Draw cell text (centered)
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

def create_text_image(text, filename, width=800, font_size=24):
    """テキストを画像として生成"""
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", font_size)
    except:
        font = ImageFont.load_default()
    
    # Create temporary image to measure text
    temp_img = Image.new('RGB', (1, 1), 'white')
    temp_draw = ImageDraw.Draw(temp_img)
    
    lines = text.split('\n')
    line_height = font_size + 10
    height = len(lines) * line_height + 40
    
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    y = 20
    for line in lines:
        draw.text((20, y), line, fill='black', font=font)
        y += line_height
    
    img.save(filename)
    return filename

def create_scanned_pdf():
    output_dir = 'c:/git/MarkBridge/TestFiles'
    pdf_path = os.path.join(output_dir, 'ocr_scan_test.pdf')
    
    # Create canvas
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    # Title as image
    title_img = create_text_image(
        "OCRテスト用スキャンドキュメント\n\n作成日: 2024年12月25日\nこのPDFは画像ベースです。OCRでテキスト抽出が必要です。",
        os.path.join(output_dir, 'temp_title.png'),
        width=700
    )
    c.drawImage(title_img, 2*cm, height - 5*cm, width=14*cm, preserveAspectRatio=True)
    
    # Section 1 header
    section1_img = create_text_image(
        "1. 表（テーブル）認識テスト",
        os.path.join(output_dir, 'temp_section1.png'),
        width=600, font_size=28
    )
    c.drawImage(section1_img, 2*cm, height - 7*cm, width=10*cm, preserveAspectRatio=True)
    
    # Table 1 as image
    table1_data = [
        ['項目', '説明', '価格'],
        ['商品A', '高品質な製品', '¥1,200'],
        ['商品B', 'スタンダード製品', '¥800'],
        ['商品C', 'エコノミー製品', '¥500'],
    ]
    table1_img = create_table_image(
        table1_data, 
        os.path.join(output_dir, 'temp_table1.png'),
        col_widths=[120, 200, 120]
    )
    c.drawImage(table1_img, 2*cm, height - 13*cm, width=12*cm, preserveAspectRatio=True)
    
    # Section 2 header
    section2_img = create_text_image(
        "2. 数値データ表",
        os.path.join(output_dir, 'temp_section2.png'),
        width=400, font_size=28
    )
    c.drawImage(section2_img, 2*cm, height - 15*cm, width=8*cm, preserveAspectRatio=True)
    
    # Table 2 as image
    table2_data = [
        ['年度', 'Q1', 'Q2', 'Q3', 'Q4', '合計'],
        ['2022', '1,234', '2,345', '3,456', '4,567', '11,602'],
        ['2023', '1,500', '2,800', '3,200', '5,100', '12,600'],
        ['2024', '1,800', '3,100', '4,200', '5,500', '14,600'],
    ]
    table2_img = create_table_image(
        table2_data, 
        os.path.join(output_dir, 'temp_table2.png'),
        col_widths=[80, 80, 80, 80, 80, 100]
    )
    c.drawImage(table2_img, 2*cm, height - 22*cm, width=14*cm, preserveAspectRatio=True)
    
    # Section 3 - Text content
    section3_img = create_text_image(
        "3. テキスト認識テスト\n\n日本語: これは日本語の文章です。\nEnglish: This is an English sentence.\n\n• 箇条書き項目1\n• 箇条書き項目2\n• 箇条書き項目3",
        os.path.join(output_dir, 'temp_section3.png'),
        width=600
    )
    c.drawImage(section3_img, 2*cm, height - 28*cm, width=12*cm, preserveAspectRatio=True)
    
    c.save()
    
    # Cleanup temp files
    for f in ['temp_title.png', 'temp_section1.png', 'temp_table1.png', 
              'temp_section2.png', 'temp_table2.png', 'temp_section3.png']:
        try:
            os.remove(os.path.join(output_dir, f))
        except:
            pass
    
    print(f"Scanned PDF created: {pdf_path}")
    print("This PDF contains images only - OCR is required to extract text!")

if __name__ == "__main__":
    create_scanned_pdf()
