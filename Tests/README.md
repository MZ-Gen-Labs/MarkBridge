# MarkBridge テストフレームワーク

## 概要
Python環境構築・OCR変換スクリプトのテスト用フレームワークです。
**本体スクリプト（`Resources/Python/`）をそのままテストで使用します。**

## 前提条件
- Docling venvがインストール済み（`%LOCALAPPDATA%\MarkBridge\.venv_docling`）

## ディレクトリ構成
```
Tests/
├── test_config.py      # 共通設定（パス定義・ヘルパー）
├── run_tests.py        # 統合テストランナー
├── test_*.py           # 各テストスクリプト
├── Fixtures/           # テスト用固定ファイル
└── Output/             # テスト出力（.gitignore対象）
```

## 使い方

### 全テスト実行
```powershell
cd Tests
& "$env:LOCALAPPDATA\MarkBridge\.venv_docling\Scripts\python.exe" run_tests.py
```

### 単一テスト実行
```powershell
& "$env:LOCALAPPDATA\MarkBridge\.venv_docling\Scripts\python.exe" test_environment.py
& "$env:LOCALAPPDATA\MarkBridge\.venv_docling\Scripts\python.exe" test_rapidocr_v5.py
```

### クイックテスト（変換スキップ）
```powershell
& "$env:LOCALAPPDATA\MarkBridge\.venv_docling\Scripts\python.exe" run_tests.py --quick
```

## テスト一覧
| ファイル | 説明 |
|----------|------|
| `test_environment.py` | Python環境・パッケージ診断 |
| `test_rapidocr_v5.py` | PP-OCRv5スタンドアロンテスト |
| `test_docling_v5.py` | Docling+PP-OCRv5統合テスト |

## 本体スクリプトとの同期
`test_config.py`で`Resources/Python/`をパスに追加しているため、
テストスクリプトから直接本体スクリプトをインポートできます：
```python
import test_config  # パス設定
import docling_v5_convert  # 本体スクリプト
```
