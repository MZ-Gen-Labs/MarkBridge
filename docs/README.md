# MarkBridge

ファイルからMarkdownへの変換を行うデスクトップGUIアプリケーション。

## 概要

MarkBridgeは、Microsoft「MarkItDown」ライブラリおよびDoclingを使用して、PDF、Word、Excel、PowerPointなど様々な形式のファイルをMarkdownに変換します。

## 機能

- **Convert**: ファイルのドラッグ＆ドロップによる一括変換
- **Files & Editor**: Markdownファイルの管理と編集
- **Settings**: Python環境とアプリケーション設定

## 技術スタック

- .NET 8 MAUI Blazor Hybrid
- Bootstrap 5
- Python (MarkItDown, Docling)

## ドキュメント

| ファイル | 内容 |
|----------|------|
| [SPECIFICATION.md](SPECIFICATION.md) | UI/UX仕様書 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 技術アーキテクチャ |
| [PYTHON_ENVIRONMENT.md](PYTHON_ENVIRONMENT.md) | Python環境管理 |
| [MAUI_BLAZOR_GUIDE.md](MAUI_BLAZOR_GUIDE.md) | MAUI Blazor開発ガイド（一般） |
| [GITHUB_BUILD.md](GITHUB_BUILD.md) | GitHub公開・ビルドガイド |

## クイックスタート

```powershell
cd c:\git\MarkBridge
dotnet run
```

## ライセンス

MIT License
