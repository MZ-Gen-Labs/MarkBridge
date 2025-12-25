# PaddleOCR 選定妥当性評価レポート

**作成日**: 2025年12月25日  
**対象プロジェクト**: MarkBridge  
**対象ブランチ**: PaddleOCR統合開発ブランチ  

---

## 1. エグゼクティブサマリー

PaddleOCR（PP-Structure V3）の選定は、**技術的要件**、**ライセンス要件**、**機能要件**の全てにおいて妥当であると評価します。

### 評価結果

| 評価項目 | 結果 | 詳細 |
|----------|------|------|
| **ライセンス適合性** | ✅ 最適 | Apache 2.0 Licenseで商用利用可能 |
| **機能適合性** | ✅ 最適 | PP-Structureによる表・レイアウト認識が強力 |
| **日本語精度** | ⭐⭐⭐⭐ | PP-OCRv5は多言語高精度（簡体字フォント表示の制限あり） |
| **統合容易性** | ✅ 良好 | 既存のPython venv環境との親和性が高い |
| **GPU対応** | ✅ 優秀 | CUDA 12.9対応で最新GPU（RTX 50）をサポート |

---

## 2. 選定理由の検証

### 2.1 ライセンス要件の検証

仕様書の記載どおり、**Apache 2.0 License** は商用利用において最も柔軟性のあるライセンスです。

| OCRエンジン | ライセンス | 商用利用 | 派生物公開義務 |
|-------------|-----------|---------|----------------|
| **PaddleOCR** | Apache 2.0 | ✅ 可能 | ❌ 不要 |
| EasyOCR | Apache 2.0 | ✅ 可能 | ❌ 不要 |
| Tesseract | Apache 2.0 | ✅ 可能 | ❌ 不要 |
| **Surya** | **GPL v3+** | ⚠️ 制限あり | ✅ **必須** |
| RapidOCR | Apache 2.0 | ✅ 可能 | ❌ 不要 |

> [!IMPORTANT]
> **Surya OCR** は高精度なドキュメント解析能力を持つが、**GPL v3ライセンス**のため採用不可。GPL v3はソースコード公開義務があり、MarkBridgeのような商用デスクトップアプリケーションには適さない。

### 2.2 機能要件の検証

#### PP-Structure V3の強み

| 機能 | PaddleOCR (PP-Structure) | Docling | EasyOCR |
|------|--------------------------|---------|---------|
| レイアウト解析 | ✅ ネイティブ対応 | ✅ DocLayNetモデル | ❌ テキスト抽出のみ |
| 表構造認識 | ✅ **SLANeXt** (高精度) | ✅ TableFormer | ❌ 非対応 |
| 数式認識 | ✅ 対応 | ✅ 対応 | ❌ 非対応 |
| Markdown出力 | ✅ `save_to_markdown` | ✅ 対応 | ❌ JSON/テキストのみ |
| 読み順復元 | ✅ 対応 | ✅ 対応 | ❌ 非対応 |

> [!TIP]
> PP-Structureは「テキスト」「表」「画像」「数式」の領域を自動検出し、それぞれに最適な処理を適用する統合パイプラインを持つ。単純なOCRエンジン（EasyOCR / Tesseract）とは根本的に設計思想が異なる。

### 2.3 日本語認識精度の検証

仕様書に記載された精度比較を、Web調査結果と照合しました：

| エンジン | 日本語精度 (主観) | 複雑レイアウト | 縦書き | ファインチューニング |
|----------|------------------|---------------|--------|---------------------|
| **PaddleOCR (PP-OCRv5)** | ⭐⭐⭐⭐⭐ | ✅ 優秀 | ✅ 対応 | 可能（やや複雑） |
| EasyOCR | ⭐⭐⭐⭐ | ⚠️ 中程度 | ⚠️ 限定的 | 容易 |
| Tesseract | ⭐⭐⭐ | ❌ 苦手 | ❌ 苦手 | 困難（ドキュメント不足） |
| Surya | ⭐⭐⭐⭐⭐ | ✅ 優秀 | ✅ 対応 | 可能 |

### 2.4 既知の制限事項

仕様書に記載された制限事項は妥当です：

| 制限事項 | 影響度 | 回避策 |
|----------|--------|--------|
| 初回モデルダウンロード（約200MB） | 低 | 一度のみ。進捗表示で対応済み |
| 簡体字フォント表示 | 中 | Markdownビューワー側でフォント指定可能 |
| nvidia pip依存 | 低 | DLLパス動的注入で対応済み |

---

## 3. 代替選択肢の評価

### 3.1 オープンソース選択肢

#### (A) EasyOCR（現在Doclingで採用中）

| 項目 | 評価 |
|------|------|
| **強み** | シンプルなAPI、GPU対応、80言語以上サポート |
| **弱み** | レイアウト解析・表認識能力なし |
| **適用場面** | スキャンPDFの文字抽出（Docling経由） |
| **MarkBridgeでの位置づけ** | Doclingエンジンの内部OCRとして採用済み |

> [!NOTE]
> EasyOCRは**単純なOCR（文字認識）** に特化しており、PP-Structureのようなドキュメント構造解析機能はない。MarkBridgeでは用途に応じて使い分けるのが最適。

#### (B) Tesseract

| 項目 | 評価 |
|------|------|
| **強み** | 長い歴史、広い言語サポート |
| **弱み** | 外部インストール必須、複雑レイアウト・日本語縦書きに弱い |
| **結論** | ❌ MarkBridgeの要件に不適合 |

#### (C) Surya OCR

| 項目 | 評価 |
|------|------|
| **強み** | 最高水準の精度、レイアウト解析、表認識 |
| **弱み** | **GPL v3ライセンス**（商用利用制限）、GPU必須傾向 |
| **結論** | ❌ ライセンス要件により採用不可 |

#### (D) Docling（IBM Research）

| 項目 | 評価 |
|------|------|
| **強み** | DocLayNet + TableFormerによる高品質構造解析、AI統合 |
| **弱み** | 内部OCRエンジン（EasyOCR）に依存 |
| **MarkBridgeでの位置づけ** | ✅ 既に主力エンジンとして採用済み |

### 3.2 商用OCR API選択肢

高精度な商用APIも検討対象として調査しました：

| サービス | 価格（1,000ページ） | 無料枠 | 日本語 | 特徴 |
|----------|---------------------|--------|--------|------|
| **Google Cloud Vision** | $1.50~ | 1,000ユニット/月 | ✅ | 高精度、シンプル |
| **Azure AI Document Intelligence** | $1.50~$50 | 500ページ/月 | ✅ | 表・フォーム抽出に強い |
| **AWS Textract** | $1.50~$50 | 1,000ページ/3ヶ月 | ✅ | 請求書・ID特化機能 |

#### 商用APIを採用しなかった理由

| 理由 | 詳細 |
|------|------|
| **コスト構造** | ページ単位課金のため大量処理でコスト増大 |
| **ネットワーク依存** | オフライン環境で使用不可 |
| **レイテンシ** | ネットワーク往復による遅延 |
| **プライバシー** | ドキュメントを外部送信する必要あり |
| **設計方針** | MarkBridgeは**ローカル完結型**を志向 |

> [!TIP]
> 将来的に「クラウドOCR連携オプション」として Azure AI Document Intelligence などを追加することは技術的に可能。需要があれば検討の価値あり。

---

## 4. エンジン選択肢と使い分け

現在のMarkBridgeは、5つのエンジンから選択可能：

```
変換エンジン選択肢
├── MarkItDown      → _it.md   : 高速・軽量（OCRなし）
├── Docling (CPU)   → _dlc.md  : 高度PDF解析 + EasyOCR/RapidOCR
├── Docling (GPU)   → _dlg.md  : CUDA加速処理
├── PaddleOCR (CPU) → _pdc.md  : PP-Structure V3（表・レイアウト特化）
└── PaddleOCR (GPU) → _pdg.md  : CUDA 12.9対応
```

### DoclingのOCRエンジン選択

EasyOCRとRapidOCRの両方を選択すると、別々のキューアイテムが作成される：

| 選択 | 出力サフィックス | 例 |
|------|------------------|-----|
| Docling CPU + EasyOCR | `_dlce.md` | `report_dlce.md` |
| Docling CPU + RapidOCR | `_dlcr.md` | `report_dlcr.md` |
| Docling GPU + EasyOCR | `_dlge.md` | `report_dlge.md` |
| Docling GPU + RapidOCR | `_dlgr.md` | `report_dlgr.md` |

### 推奨使い分け

| ドキュメント種別 | 推奨エンジン | 理由 |
|------------------|--------------|------|
| テキストベースPDF | MarkItDown | 高速・正確 |
| 複雑レイアウトPDF | Docling / PaddleOCR | 構造解析能力 |
| **表が多いドキュメント** | **PaddleOCR** | SLANeXtモデルの表認識精度 |
| スキャンPDF（主にテキスト） | Docling + EasyOCR | OCR精度 |
| **高速OCR処理** | Docling + RapidOCR | 軽量高速 |
| **日本語ビジネス文書** | **PaddleOCR** | 日本語+表+レイアウト |

---

## 5. 実装品質の評価

### 5.1 コード品質

[paddle_convert.py](file:///c:/git/MarkBridge/Resources/Python/paddle_convert.py) の実装を確認しました：

| 項目 | 評価 | コメント |
|------|------|----------|
| DLL依存関係解決 | ✅ 優秀 | nvidia/torch DLLパスを動的注入 |
| GPU/CPUモード切替 | ✅ 優秀 | 厳格なGPUモードでフォールバック防止 |
| PDF処理 | ✅ 良好 | PyMuPDFでページ単位処理 |
| エラーハンドリング | ✅ 良好 | try-except + traceback |
| 一時ファイル管理 | ✅ 良好 | UUID付き一時ディレクトリ + クリーンアップ |

### 5.2 アーキテクチャ適合性

[ConversionService.cs](file:///c:/git/MarkBridge/Services/ConversionService.cs) の `RunPaddleOcrAsync` メソッド：

```csharp
var args = $"\"{scriptPath}\" \"{inputPath}\" \"{outputPath}\" --lang japan";
if (useGpu)
{
    args += " --use_gpu";
}
```

- 既存のDocling/MarkItDown処理と同じパターンを踏襲
- Python仮想環境を適切に利用
- 非同期処理でUIをブロックしない設計

---

## 6. 結論と推奨事項

### 6.1 結論

**PaddleOCR（PP-Structure V3）の選定は妥当**です。

| 評価観点 | 結論 |
|----------|------|
| ライセンス | ✅ Apache 2.0で商用利用問題なし |
| 機能 | ✅ 表・レイアウト認識でDoclingを補完 |
| 日本語精度 | ✅ EasyOCR/Tesseractより優秀 |
| 実装品質 | ✅ 既存アーキテクチャとの整合性良好 |
| 代替選択肢 | ✅ Suryaはライセンス不可、商用APIはローカル完結の方針に反する |

### 6.2 推奨事項

| 優先度 | 推奨事項 |
|--------|----------|
| 高 | 簡体字フォント問題の緩和（HTMLラッパーでフォント指定） |
| 中 | ユーザー向けエンジン選択ガイドの作成 |
| 低 | 将来的なクラウドOCR連携オプションの検討 |

---

## 7. 参考資料

- [dev_summary_paddleocr.md](file:///c:/git/MarkBridge/docs/dev_summary_paddleocr.md) - 開発サマリー
- [SPECIFICATION.md](file:///c:/git/MarkBridge/docs/SPECIFICATION.md) - 要求仕様書
- [ARCHITECTURE.md](file:///c:/git/MarkBridge/docs/ARCHITECTURE.md) - 技術アーキテクチャ
- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR) - 公式リポジトリ
- [PP-Structure Documentation](https://paddleocr.ai/) - PP-Structure公式ドキュメント
