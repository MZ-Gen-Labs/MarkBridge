# GitHub公開・ビルドガイド

MarkBridgeリポジトリのGitHub公開とGitHub Actionsによる自動ビルド・リリースに関する技術情報。

---

## 1. リポジトリ構成

```
MarkBridge/
├── .github/
│   └── workflows/
│       └── release.yml      # リリース自動化ワークフロー
├── docs/                    # ドキュメント
├── README.md                # プロジェクト説明
├── LICENSE                  # MITライセンス
└── MarkBridge.csproj        # プロジェクトファイル
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
5. `dotnet publish` - ビルド・発行
6. `Compress-Archive` - ZIP作成
7. `softprops/action-gh-release@v1` - GitHub Releaseへアップロード

### 2.2 リリースの作成方法

```powershell
# バージョンタグを作成してプッシュ
git tag v0.0.2
git push origin v0.0.2
```

タグプッシュ後、自動でビルドが実行され、Releasesページにバイナリがアップロードされます。

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

### フレームワーク依存（Framework-dependent）

```powershell
dotnet publish -c Release -r win-x64 --no-self-contained -o ./publish
```

- **サイズ:** 約20-30MB
- **要件:** .NET 8 Runtimeが別途必要
- **推奨:** 一般的なケース

### 自己完結型（Self-contained）

```powershell
dotnet publish -c Release -r win-x64 --self-contained -o ./publish
```

- **サイズ:** 約150-200MB
- **要件:** なし（.NETランタイム同梱）
- **推奨:** ランタイムインストール不可の環境向け

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

## 7. 参考リンク

- [GitHub Actions公式ドキュメント](https://docs.github.com/ja/actions)
- [.NET MAUI CI/CDガイド](https://learn.microsoft.com/ja-jp/dotnet/maui/deployment/)
- [softprops/action-gh-release](https://github.com/softprops/action-gh-release)
