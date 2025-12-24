# MarkBridge

[![Build](https://github.com/MZ-Gen-Labs/MarkBridge/actions/workflows/build.yml/badge.svg)](https://github.com/MZ-Gen-Labs/MarkBridge/actions/workflows/build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ファイルからMarkdownへの変換を行うWindows向けデスクトップGUIアプリケーション。

## 概要

MarkBridgeは、Microsoft「[MarkItDown](https://github.com/microsoft/markitdown)」および「[Docling](https://github.com/docling-project/docling)」を使用して、PDF、Word、Excel、PowerPointなど様々な形式のファイルをMarkdownに変換するツールです。

### 主な機能

- **🔄 Convert** - ドラッグ＆ドロップによるファイル一括変換
- **📝 Files & Editor** - 変換結果のMarkdownファイル管理・編集
- **⚙️ Settings** - Python環境とアプリケーション設定

### 変換エンジン

| エンジン | 説明 |
|----------|------|
| MarkItDown | 標準・高速・軽量な変換 |
| Docling (CPU) | 高度なPDF解析、OCR対応 |
| Docling (GPU) | CUDA対応GPU高速処理 |

## システム要件

| 項目 | 要件 |
|------|------|
| OS | Windows 10 (19041+) / Windows 11 |
| .NET | .NET 8 Runtime |
| Python | 3.10以上（アプリ内でインストール可能） |
| GPU（オプション） | NVIDIA RTXシリーズ推奨 |

## インストール

### リリースからダウンロード

1. [Releases](../../releases) ページから最新版のZIPファイルをダウンロード
2. 任意のフォルダに展開
3. `MarkBridge.exe` を実行

> **Note:** .NET 8 Runtime が必要です。インストールされていない場合は、[.NET 8 ダウンロードページ](https://dotnet.microsoft.com/download/dotnet/8.0)からインストールしてください。

### 初回セットアップ

1. アプリを起動し **Settings** タブを開く
2. Python Install Managerがインストールされていない場合は、案内に従ってインストール
3. 必要なPythonバージョンを選択してインストール
4. **Virtual Environment** セクションで [Create] をクリック
5. 必要なライブラリ（MarkItDown、Docling等）をインストール

## 開発者向け

### ビルド

```powershell
git clone https://github.com/MZ-Gen-Labs/MarkBridge.git
cd MarkBridge
dotnet build
dotnet run
```

### リリースビルド

```powershell
dotnet publish -c Release -r win10-x64 --no-self-contained
```

## 技術スタック

- .NET 8 MAUI Blazor Hybrid
- Bootstrap 5
- BlazorMonaco (Markdownエディタ)
- Python (MarkItDown, Docling)

## ドキュメント

| ファイル | 内容 |
|----------|------|
| [SPECIFICATION.md](docs/SPECIFICATION.md) | UI/UX仕様書 |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 技術アーキテクチャ |
| [PYTHON_ENVIRONMENT.md](docs/PYTHON_ENVIRONMENT.md) | Python環境管理 |
| [MAUI_BLAZOR_GUIDE.md](docs/MAUI_BLAZOR_GUIDE.md) | MAUI Blazor開発ガイド |

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

---

**Note:** このアプリケーションは外部ツールとして [MarkItDown](https://github.com/microsoft/markitdown) (MIT License) および [Docling](https://github.com/docling-project/docling) (MIT License) を使用しています。
