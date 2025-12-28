# 画像出力仕様 (Image Export Specification)

MarkBridgeの各変換エンジンにおける画像出力の仕様をまとめます。

## 対象エンジン

| エンジン | 画像出力サポート | オプション設定 |
|---------|-----------------|---------------|
| MarkItDown | ❌ なし | - |
| Docling (CPU/GPU) | ✅ あり | 3モード選択可 |
| PaddleOCR (CPU/GPU) | ❌ なし | - |
| Marker (CPU/GPU) | ✅ あり | 自動（外部ファイル） |

---

## Docling の画像出力

### 出力モード

Doclingは `--image-export-mode` オプションで3つのモードをサポート：

| モード | CLI引数 | 説明 |
|-------|---------|------|
| **None** | `placeholder` | 画像を出力しない（プレースホルダーのみ） |
| **Embedded** | `embedded` | Base64埋め込み（Markdownファイル内に直接埋め込み） |
| **ExternalFiles** | `referenced` | 外部ファイル出力（画像は別ファイルとして保存） |

### 画像ファイルの出力場所

`ExternalFiles (referenced)` モード選択時：

1. **同一ディレクトリ**: 直接`.png`, `.jpg`等が出力される場合あり
2. **imagesサブディレクトリ**: `images/` フォルダに格納される場合あり

```
Output/
├── document.md
├── image_001.png         # 直接配置パターン
└── images/
    ├── image_002.png     # サブディレクトリパターン
    └── image_003.jpg
```

### Docling特有の挙動

1. **OCR無効時のテーブル画像化**
   - `--no-ocr` オプション使用時、テーブル要素が `Picture` として扱われ、画像化される
   - テーブル内の文字情報は失われる

2. **OCR有効時のテーブル抽出**
   - OCR有効時はテーブルがMarkdown形式で抽出される
   - 画像は図（Figure）のみが対象

3. **画像命名規則**
   - `image_001.png`, `image_002.png` のような連番
   - 元のPDF内の位置や種類に基づかない

---

## Marker の画像出力

### 出力方式

Markerは自動的に画像を外部ファイルとして出力：

```
Output/
├── document.md
└── document/
    ├── document.md       # 重複（Marker仕様）
    ├── document_meta.json
    ├── image_0.jpeg
    └── image_1.png
```

### MarkBridgeでの処理

1. Markerの出力フォルダから `.md` ファイルを最終出力先に移動
2. 画像ファイルは `[filename]_images/` サブフォルダにコピー
3. Markdown内の画像リンクを書き換え

```markdown
<!-- 書き換え前（Marker出力） -->
![](document/image_0.jpeg)

<!-- 書き換え後（MarkBridge処理） -->
![](document_images/image_0.jpeg)
```

### オプション

- `--disable_image_extraction`: 画像抽出を無効化

---

## 実装参照

| ファイル | 説明 |
|---------|------|
| `Services/ConversionService.cs` | 変換ロジック・画像コピー処理 |
| `Services/AppStateService.cs` | `ImageExportMode` enum定義 |
| `Components/Pages/Convert.razor` | UIオプション選択 |

---

## 既知の制限事項

### Docling
- OCR無効時にテーブルが画像化される（テキスト抽出不可）
- 画像命名が汎用的（元の画像名を保持しない）

### Marker
- 常に外部ファイル出力（Embedded/Noneモードなし）
- 出力フォルダ構造が固定（`filename/filename.md`）

---

## 関連Issue

- [#4 Image Export (Files) の画像出力表示検証](https://github.com/MZ-Gen-Labs/MarkBridge/issues/4)
