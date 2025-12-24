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

### 2.2 非同期処理

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
| Docling (CPU) | 高度PDF解析、OCR対応 | `_dl.md` |
| Docling (GPU) | GPU高速処理（CUDA必須） | `_dlc.md` |

- 1つ以上のエンジン選択必須
- 複数選択時は各エンジンで並列変換

> **注意:** Docling (GPU)使用には事前にCUDA版PyTorchのインストールが必要。インストール後はアプリの再起動が必要。

#### エンジンオプション（Docling選択時のみ有効）

- Enable OCR: スキャンPDF用文字認識
- Include Images: 画像抽出・サブフォルダ保存

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
- ファイル操作: 閲覧、作成、削除、名前変更、移動

#### 右ペイン: Markdown Editor

- BlazorMonaco（ローカル同梱）
- Edit / Previewモード切替
- 書式ツールバー（太字、見出し、リスト、リンク、コード）

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

#### 2. Virtual Environment Area

- パス表示・変更（Browse...）
- ステータス: ✅ exists / ⬜ not found
- ボタン: venv未存在時 [Create] / 存在時 [Delete]

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