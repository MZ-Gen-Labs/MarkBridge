# MarkBridge 要求仕様書

## 1. 概要

MarkBridgeは、Microsoft製「MarkItDown」ライブラリおよびDoclingを利用し、様々な形式のファイルをMarkdownへ変換するデスクトップGUIアプリケーションである。

### 対象ユーザー

- 技術文書をMarkdownで管理したいユーザー
- PDF/Office文書をテキスト化したいユーザー
- コマンドライン操作なしでファイル変換を行いたいユーザー

---

## 2. UI/UX方針

### 2.1 デザイン

- Microsoft Fluent Design Systemに準拠
- ダークモード/ライトモード対応（Bootstrap 5 `data-bs-theme`）
- 画面上部のタブナビゲーション（Convert / Files & Editor / Settings）
- 画面下部にステータスバー（処理状態、venv状態表示）

### 2.2 起動時初期化

起動時にローディング画面を表示し、以下の初期化が完了するまで操作をブロック:

1. 設定ファイル読み込み
2. Pythonインストール確認
3. 仮想環境確認
4. パッケージ確認（venv有効時）

初期化中は「設定を読み込み中...」「Python環境を確認中...」等のステータスメッセージを表示。

### 2.3 非同期処理

- 時間のかかる処理（変換、インストール等）は非同期実行
- 処理中はスピナー/プログレスバーを表示
- UIをブロックしない

### 2.3 エラー通知

| 種別 | 表示方法 |
|------|----------|
| 軽微なエラー | トースト通知（5秒後自動消滅） |
| 詳細確認 | トーストの「詳細」→モーダルダイアログ |
| 重大エラー | 即時モーダルダイアログ |

### 2.4 確認ダイアログ

全ての破壊的操作（削除、インストール等）は実行前に確認ダイアログを表示し、キャンセル可能。

---

## 3. 画面仕様

### 3.1 Convertタブ

ファイル変換のメイン画面。

#### ドラッグ＆ドロップエリア

- ファイル/フォルダをドロップして変換キューに追加
- Win32 API経由で実装（完全なファイルパス取得）
- フォルダドロップ時はサブフォルダ含有の確認ダイアログ

#### 変換エンジン選択（チェックボックス - 複数選択可）

| エンジン | 説明 | 出力サフィックス |
|----------|------|------------------|
| MarkItDown | 標準、高速、軽量 | `_it.md` |
| Docling (CPU) | 高度PDF解析、OCR対応 | `_dlc.md` |
| Docling (GPU) | GPU高速処理（CUDA必須） | `_dlg.md` |
| PaddleOCR (CPU) | 表・レイアウト解析特化（PP-Structure） | `_pdc.md` |
| PaddleOCR (GPU) | CUDA 12.9対応GPU版 | `_pdg.md` |
| Marker (CPU) | 高精度PDF変換、テーブル認識優秀 | `_mkc.md` |
| Marker (GPU) | GPU高速処理（CUDA 12.8 Nightly） | `_mkg.md` |

- 1つ以上のエンジン選択必須
- 複数選択時は各エンジンで並列変換
- Markerエンジンは **Advanced Engines** セクション（要ライセンス同意）で有効化

> **注意:** GPU版エンジン使用には事前にCUDA版パッケージのインストールが必要。

#### 拡張子命名規則

```
ファイル名_[エンジン][c/g][e/r/v].md
```

| 記号 | 意味 |
|------|------|
| `c` | CPU版 |
| `g` | GPU版 |
| `e` | EasyOCR使用 |
| `r` | RapidOCR使用 |
| `v` | RapidOCR v5使用 |

**Docling + OCRエンジンの例:**
- `_dlce.md` = Docling CPU + EasyOCR
- `_dlcr.md` = Docling CPU + RapidOCR
- `_dlge.md` = Docling GPU + EasyOCR
- `_dlgr.md` = Docling GPU + RapidOCR
- `_dlgv.md` = Docling GPU + RapidOCR v5

#### エンジンオプション（Docling選択時）

- **Enable OCR**: スキャンPDF用文字認識
  - **Force OCR**: 全ページに強制的にOCR処理を適用（`--force-ocr`）
- **OCR Engine**: 下記から選択（複数選択で複数のキューアイテム作成）
  - EasyOCR (GPU, 80+ languages) - 深層学習ベース高精度
  - RapidOCR (faster, lightweight) - 軽量高速
  - **RapidOCR v5 (Japanese optimized)** - PP-OCRv5モデル使用、日本語高精度
- **Image Export**: 画像エクスポートモード
  - None: 画像なし（プレースホルダーのみ）
  - Embedded: Base64でMarkdown内に埋め込み
  - Files: 外部ファイルとして保存（サブフォルダ作成）

> **詳細:** 画像出力の詳細仕様は [IMAGE_EXPORT.md](IMAGE_EXPORT.md) を参照。

#### エンジンオプション（Marker選択時）

- **Disable OCR**: OCR処理を無効化
- **Disable image extraction**: 画像抽出を無効化

> **注意:** Marker (GPU) はPyTorch CUDA 12.8 Nightlyが必要（RTX 50シリーズ対応）。

#### OCRエンジン仕様

Doclingでは3種類のOCRエンジンを選択可能。日本語と英語を同時認識（`--ocr-lang ja,en`）。

| エンジン | 精度 | 速度 | 日本語 | 特徴 |
|----------|------|------|--------|------|
| **EasyOCR** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 深層学習ベース、80言語以上 |
| **RapidOCR** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 軽量高速、PP-OCRv3ベース |
| **RapidOCR v5** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | PP-OCRv5モデル、18K文字辞書、日本語最適化 |

> **RapidOCR v5について:** Doclingパイプライン内でRapidOCRエンジンにPP-OCRv5モデルを設定して使用。テーブル構造認識（TableFormer）を維持しつつ、高精度な日本語OCRを実現。

> **複数選択時の動作:** 複数のOCRエンジンをチェックすると、同一ファイルに対して複数の変換キューアイテムが作成され、それぞれのOCRエンジンで処理される。

**Force OCR:**
全ページに対して強制的にOCR処理を適用。スキャンPDFや画像埋め込みPDFに有効。処理時間は長くなるが精度向上。

**インストール方法:**
Settings画面で「Install EasyOCR」ボタンをクリック（`docling[easyocr]`として自動インストール）

#### 出力設定

- 元のファイルと同じフォルダ
- 特定のフォルダを指定（Browse...）
- 同時変換数: スライダー（1～10、デフォルト: 3）

#### Conversion Queue

| カラム | 内容 |
|--------|------|
| ☑️ | 選択チェックボックス |
| Name | ファイル名 + 出力サフィックス |
| Engine | 変換エンジンバッジ |
| File Type | ファイル種別バッジ |
| Path | ファイルパス |
| Status | Queued / Converting / Completed (Xs) / Failed |
| × | 削除ボタン |

> **実装:** 複数エンジン選択時、ファイル追加時にエンジンごとのキューアイテムが作成される（例: 1ファイル × 3エンジン = 3アイテム）。Completed時は経過時間を表示。

#### アクションボタン

- Start Selected Conversions
- Pause / Cancel
- Remove Selected / Clear All

#### Conversion Errors

変換失敗時にキューの下にエラーメッセージを表示:
- ダークテーマ背景でコピー可能
- ファイル名とエラー内容を表示
- デバッグやトラブルシューティングに役立つ詳細情報を含む

#### 並列処理仕様

- SemaphoreSlimで同時変換数を制御
- 各キューアイテムはTask.Runで並列実行
- Doclingは一時ディレクトリで出力後、最終ファイル名にリネーム

> **パフォーマンス注意:** Docling CPUとGPUの同時実行はCPUリソース競合により性能低下が発生する場合がある。最高性能を得るにはGPU単独実行を推奨。

---

### 3.2 Files & Editorタブ

ファイル管理とMarkdown編集の統合画面。

#### 左ペイン: File Explorer

- デフォルトスコープ: `Documents\MarkBridge\Output`
- ツールバー: Refresh / New Folder / Delete / Search
- **折りたたみ機能**: 左上の`◀`ボタンでパネルを折りたたみ、編集領域を拡大可能
- ファイル操作: 閲覧、作成、削除、名前変更、移動

#### 右ペイン: Markdown Editor

- BlazorMonaco（ローカル同梱）
- Edit / Previewモード切替
- 書式ツールバー（太字、見出し、リスト、リンク、コード）
- **ファイルを閉じる**: 右上の`×`ボタンで現在のファイルを閉じる
- **HTMLエクスポート**: 右上の「HTML」ボタンでスタイル付きHTMLファイルとして保存

#### Markdownプレビュー機能

Markdigライブラリで以下の拡張機能を有効化:

| 機能 | 説明 |
|------|------|
| Pipe Tables | GitHub風テーブル構文 |
| Task Lists | チェックボックスリスト |
| Auto Links | URLの自動リンク化 |
| Emphasis Extras | 取り消し線など |

#### 保存仕様

| モード | 動作 |
|--------|------|
| 手動保存 | Ctrl+S または保存ボタン |
| 自動保存 | 編集後数秒で自動保存（Settingsで切替可） |

---

### 3.3 Settingsタブ

#### 1. Python Install Manager Area

- ステータス表示: ✅ 検出済み / ⚠️ 未検出
- 未検出時: python.org/downloads へのリンク表示
- バージョン管理グリッド:

| カラム | 内容 |
|--------|------|
| Version | 3.13, 3.12, 3.11... |
| Status | ✅ Installed / ⬜ Available |
| Active | ● ラジオボタン |
| Actions | [Install] / [Uninstall] |

#### 2. Conversion Engines Area（venv分離アーキテクチャ）

各変換エンジンは独立した仮想環境を使用し、依存関係の競合（特にCUDAバージョン）を回避。

| エンジン | venvパス | 説明 |
|----------|----------|------|
| MarkItDown | `.venv_markitdown` | 標準変換、軽量 |
| Docling | `.venv_docling` | PyTorch/CUDA使用（12.4または12.8） |
| PaddleOCR | `.venv_paddle` | PaddlePaddle使用（CUDA 12.3） |
| Marker | `.venv_marker` | PyTorch/CUDA使用（12.8 Nightly） |

**Doclingインストールオプション:**

| モード | PyTorchバージョン | 用途 |
|--------|------------------|------|
| CPU | CPU版 | GPU非搭載環境 |
| GPU（推奨） | CUDA 12.4 | 通常のNVIDIA GPU |
| Nightly | CUDA 12.8 Nightly | RTX 50シリーズ対応 |

**レガシーvenv移行:**
- 旧バージョンからアップグレード時、共有`.venv`が検出されると移行ダイアログを表示
- 「Delete Legacy Venv」で古いvenvを削除
- 「Dismiss」でファイルを残してパス設定のみクリア

**各エンジンカードのUI:**
- パス表示・変更（Browse...）
- ステータス: ✅ Ready vX.X.X / ⚠️ Package not installed / ⬜ Not configured
- ボタン: Setup CPU/GPU/Nightly / Install / Reinstall / Delete

#### Advanced Engines（ライセンス確認エリア）

MarkerエンジンはCC-BY-NC-SAライセンスのため、有効化前にライセンス同意が必要。

| エンジン | ライセンス | 説明 |
|----------|-----------|------|
| Marker | CC-BY-NC-SA | 高精度PDF変換、商用利用制限あり |

**Markerインストールフロー:**
1. ライセンス条項の確認・同意
2. 「Accept and Enable Marker」でインストール有効化
3. 「Install Marker」でパッケージインストール
4. 「Add GPU (CUDA)」でPyTorch Nightly（CUDA 12.8）追加

> **GPU対応:** MarkerのGPUモードはPyTorch CUDA 12.8 Nightlyを使用。RTX 50シリーズ（sm_120）対応。インストール後、互換のためPillowを10.x系にダウングレード。

#### 3. Library Management Area

| ライブラリ | 説明 |
|------------|------|
| MarkItDown | 標準変換エンジン（`markitdown[all]`で全形式対応） |
| Docling | 高度PDF/OCR変換 |
| PyTorch (CUDA) | GPU変換用（CUDA 12.4、通常のGPU向け） |
| PyTorch Nightly | GPU変換用（CUDA 12.8 Nightly、RTX 50シリーズ向け） |

- ステータス: ✅ vX.X.X / ⬜ Not installed / 🔄 Update available
- PyTorch (CUDA) と PyTorch Nightly は排他的
- CUDAインストール後はアプリ再起動が必要

#### 4. Application Settings

- 自動保存 ON/OFF
- 言語選択（日本語/English）
- テーマ選択（ダーク/ライト）
- 同時変換数スライダー

---

## 4. 共通仕様

### 4.1 対応ファイル形式

PDF, DOCX, PPTX, XLSX, HTML, XML, JSON, CSV, EPUB, ZIP

### 4.2 変換履歴ログ

- `conversion_history.json`に保存
- 最新1000件保持
- 内容: 日時、入力/出力ファイル、エンジン、結果、エラー

### 4.3 キーボードショートカット

| ショートカット | 機能 | 対象 |
|----------------|------|------|
| Ctrl+S | 保存 | Editor |
| Ctrl+O | フォルダを開く | Editor |
| Delete | 選択削除 | Convert |
| Ctrl+A | 全選択 | Convert |
| Ctrl+Enter | 変換開始 | Convert |

---

## 5. 多言語対応

### 実装方針

- .NET `IStringLocalizer<T>` 使用
- 初期リリース: 英語のみ（フレームワークは構築済み）
- 後続リリース: 日本語対応（`Strings.ja.resx`追加）

### 翻訳対象

- 対象: 全UI文字列
- 非対象: ログ、デバッグメッセージ

---

## 6. ウィンドウ設定

| 項目 | 値 |
|------|-----|
| デフォルトサイズ | 1024×768 |
| 最小サイズ | 800×600 |
| サイズ記憶 | 終了時保存、起動時復元 |

---

## 7. 開発者向け備考

### 7.1 PowerShell文字化け対策

日本語Windows環境でPowerShellの出力が文字化けする場合、以下を実行:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

永続化するには`$PROFILE`に追加。

### 7.2 コード署名

Windowsセキュリティポリシーにより`.exe`がブロックされる場合、自己署名証明書でコード署名:

```powershell
# 1. 証明書作成（初回のみ）
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=MarkBridge Dev" -CertStoreLocation Cert:\CurrentUser\My -NotAfter (Get-Date).AddYears(5)

# 2. 信頼リストに追加
Export-Certificate -Cert $cert -FilePath ".\MarkBridge_Dev.cer"
Import-Certificate -FilePath ".\MarkBridge_Dev.cer" -CertStoreLocation Cert:\CurrentUser\Root

# 3. 署名（ビルド後自動実行 - csprojに設定済み）
```

`csproj`のPostBuildターゲットにより、Debugビルド後に自動署名される。

---

## 8. テストフレームワーク

### 8.1 構成

Python環境構築・OCR変換スクリプトのテスト用フレームワーク。**本番venvとテストvenvを分離**。

```
Tests/
├── setup_test_venv.py  # テストvenv構築スクリプト
├── test_config.py      # 共通設定（パス定義・ヘルパー）
├── run_tests.py        # 統合テストランナー
├── test_*.py           # 各テストスクリプト
├── Fixtures/           # テスト用固定ファイル
└── Output/             # テスト出力（.gitignore対象）
```

### 8.2 テストvenv分離

本番venvを汚さずにテスト可能。`test_config.py`で本番venvとテストvenvを切り替え可能。

| venv種別 | パス例 | 用途 |
|----------|--------|------|
| 本番 | `.venv_docling` | アプリ実行用 |
| テスト | `.venv_test_docling` | テスト実行用 |

**テストvenv構築:**
```powershell
cd Tests
python setup_test_venv.py setup --engine docling
python setup_test_venv.py status
python setup_test_venv.py teardown --engine docling
```

### 8.3 本体スクリプトとの連携

`test_config.py`で`Resources/Python/`をパスに追加し、本体スクリプトを直接インポート:

```python
import test_config  # パス設定
import docling_v5_convert  # 本体スクリプト
```

### 8.4 実行方法

```powershell
cd Tests
& "$env:LOCALAPPDATA\MarkBridge\.venv_docling\Scripts\python.exe" run_tests.py
```

### 8.5 テスト一覧

| テスト | 説明 |
|--------|------|
| `test_environment.py` | Python環境・パッケージ診断 |
| `test_rapidocr_v5.py` | PP-OCRv5スタンドアロンテスト |
| `test_docling_v5.py` | Docling+PP-OCRv5統合テスト |
| `test_venv_setup.py` | venv構築・削除テスト |
| `test_image_export.py` | 画像出力モードテスト |
| `test_ocr_settings.py` | OCR設定テスト |
