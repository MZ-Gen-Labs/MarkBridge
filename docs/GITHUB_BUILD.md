# GitHub公開・ビルドガイド

MarkBridgeリポジトリのGitHub公開とGitHub Actionsによる自動ビルド・リリースに関する技術情報。

---

## 1. リポジトリ構成

```
MarkBridge/
├── .github/
│   ├── installer/
│   │   └── MarkBridge.iss    # Inno Setupスクリプト
│   └── workflows/
│       └── release.yml       # リリース自動化ワークフロー
├── Resources/
│   └── AppIcon/
│       └── appicon.png       # アプリアイコン（PNG→ICO自動変換）
├── docs/                     # ドキュメント
├── README.md                 # プロジェクト説明
├── LICENSE                   # MITライセンス
└── MarkBridge.csproj         # プロジェクトファイル
```

---

## 2. GitHub Actionsワークフロー

### 2.1 リリースワークフロー（release.yml）

**トリガー:** `v*` タグのプッシュ時

```yaml
on:
  push:
    tags:
      - 'v*'
```

**主要ステップ:**

1. `actions/checkout@v4` - ソースコード取得
2. `actions/setup-dotnet@v4` - .NET 8 SDK設定
3. `dotnet workload install maui-windows` - MAUIワークロードインストール
4. `dotnet restore -r win-x64` - 依存関係復元
5. `dotnet publish` - Self-containedビルド
6. `Compress-Archive` - ZIP作成
7. `choco install imagemagick` - ImageMagickでPNG→ICO変換
8. `choco install innosetup` - Inno Setupインストール
9. `ISCC.exe` - インストーラー作成
10. `softprops/action-gh-release@v1` - GitHub Releaseへアップロード

### 2.2 リリースの作成方法

```powershell
# バージョンタグを作成してプッシュ
git tag v0.0.5
git push origin v0.0.5
```

タグプッシュ後、自動でビルドが実行され、Releasesページに以下がアップロードされます：
- `MarkBridge-X.X.X-win-x64-selfcontained.zip` - ポータブル版
- `MarkBridge-X.X.X-win-x64-setup.exe` - インストーラー版

---

## 3. .NET MAUI Blazor Hybrid × GitHub Actions の注意点

### 3.1 $(MauiVersion) 変数は使用禁止

**問題:**
```xml
<!-- ❌ GitHub Actionsでエラー -->
<PackageReference Include="Microsoft.Maui.Controls" Version="$(MauiVersion)" />
```

GitHub Actions環境では `$(MauiVersion)` 変数が定義されていないため、`error NU1015` が発生します。

**解決策:**
```xml
<!-- ✅ 固定バージョンを使用 -->
<PackageReference Include="Microsoft.Maui.Controls" Version="8.0.100" />
<PackageReference Include="Microsoft.Maui.Controls.Compatibility" Version="8.0.100" />
<PackageReference Include="Microsoft.AspNetCore.Components.WebView.Maui" Version="8.0.100" />
```

### 3.2 EnableWindowsTargeting の設定

Windows向けビルドをLinux/macOS上でも実行可能にするため、csprojに追加:

```xml
<PropertyGroup>
    <EnableWindowsTargeting>true</EnableWindowsTargeting>
</PropertyGroup>
```

### 3.3 RuntimeIdentifier の指定

ビルド時に指定する方が柔軟:

```yaml
# ワークフローでRIDを指定
- name: Restore dependencies
  run: dotnet restore -r win-x64
  
- name: Publish
  run: dotnet publish -c Release -r win-x64 --no-self-contained -o ./publish
```

csprojからは削除するか、コメントアウト:

```xml
<!-- <RuntimeIdentifier>win-x64</RuntimeIdentifier> -->
```

---

## 4. ビルド種類

### 現在の設定（Self-contained + Windows App SDK同梱）

```powershell
dotnet publish -c Release -r win-x64 --self-contained true -p:WindowsAppSDKSelfContained=true -o ./publish
```

- **サイズ:** インストーラー約50MB / ZIP約75MB
- **要件:** なし（.NETランタイム + Windows App SDK同梱）
- **メリット:** ユーザーはランタイムのインストール不要

### 参考：フレームワーク依存（Framework-dependent）

```powershell
dotnet publish -c Release -r win-x64 --no-self-contained -o ./publish
```

- **サイズ:** 約20-30MB
- **要件:** .NET 8 Runtime + Windows App Runtimeが別途必要
- **デメリット:** ユーザーがランタイムをインストールする必要がある

---

## 5. GitHub Actions制限

### 無料枠（Freeプラン）

| 項目 | パブリックリポジトリ | プライベートリポジトリ |
|------|----------------------|------------------------|
| 実行時間 | 無制限 | 2,000分/月 |
| 並列ジョブ | 20 | 20 |
| ジョブ単位制限 | 6時間 | 6時間 |

### 実行時間削減のヒント

1. **build.yml無効化** - 開発中はpush毎のビルドを無効化
2. **キャッシュ活用** - NuGetパッケージをキャッシュ
3. **タグトリガーのみ** - リリース時のみビルド実行

---

## 6. トラブルシューティング

| エラー | 原因 | 解決策 |
|--------|------|--------|
| `NU1015: PackageReference without version` | `$(MauiVersion)` 未定義 | 固定バージョン使用 |
| `RuntimeIdentifier not recognized` | `win10-x64` は非推奨 | `win-x64` を使用 |
| `dotnet workload install` 失敗 | 権限不足またはSDKバージョン | `uses: actions/setup-dotnet@v4` を確認 |
| ビルド成功だがRelease作成されない | permissions設定不足 | `permissions: contents: write` を追加 |

---

## 7. Inno Setupインストーラー

### 7.1 概要

Inno Setupを使用して、Windowsインストーラー(.exe)を自動生成します。

**生成されるファイル:**
- `MarkBridge-X.X.X-win-x64-setup.exe` - インストーラー（約50MB）
- `MarkBridge-X.X.X-win-x64-selfcontained.zip` - ポータブル版（約75MB）

### 7.2 スクリプトの場所

```
.github/installer/MarkBridge.iss
```

### 7.3 主な機能

| 機能 | 説明 |
|------|------|
| **64ビットWindows対応** | x64専用 |
| **日本語/英語対応** | 言語選択可能 |
| **アップグレードインストール** | 既存バージョンを上書き可能 |
| **設定引き継ぎ** | 前回の設定（インストール先、言語）を保持 |
| **アプリ自動終了** | 実行中のアプリを自動で閉じてインストール |
| **デスクトップアイコン** | オプションで作成可能 |
| **スタートメニュー登録** | プログラムグループに登録 |
| **アンインストーラー付属** | 完全削除可能 |

### 7.4 アップグレードの仕組み

固定の`AppId`を使用することで、同じアプリとして認識されます：

```iss
AppId={{8A4D6F2E-3B5C-4A1D-9E8F-7C2B1A0D5E6F}
```

**ユーザーの操作:**
1. 新しい`setup.exe`をダウンロード
2. 実行するだけ（アンインストール不要）
3. 既存ファイルが新バージョンで上書きされる

### 7.5 アイコンの生成

GitHub Actions上でImageMagickを使用してPNGからICOを自動生成：

```yaml
- name: Install ImageMagick and create ICO
  run: |
    choco install imagemagick -y --no-progress
    magick "Resources\AppIcon\appicon.png" -define icon:auto-resize=256,128,64,48,32,16 "Resources\AppIcon\appicon.ico"
```

### 7.6 GitHub Actionsでの実行

```yaml
- name: Install Inno Setup
  run: choco install innosetup -y --no-progress

- name: Build Installer
  run: |
    & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DMyAppVersion="${{ steps.version.outputs.VERSION }}" ".github\installer\MarkBridge.iss"
```

---

## 8. 参考リンク

- [GitHub Actions公式ドキュメント](https://docs.github.com/ja/actions)
- [.NET MAUI CI/CDガイド](https://learn.microsoft.com/ja-jp/dotnet/maui/deployment/)
- [softprops/action-gh-release](https://github.com/softprops/action-gh-release)
