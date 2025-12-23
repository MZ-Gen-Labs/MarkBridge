# MarkBridge 技術アーキテクチャ

## 1. 技術スタック

| 技術 | 用途 |
|------|------|
| .NET 8 MAUI Blazor Hybrid | アプリケーションフレームワーク |
| Bootstrap 5 | UIスタイリング（CDN） |
| BlazorMonaco | Markdownエディタ（ローカル同梱） |
| Markdig | Markdown→HTMLレンダリング |
| Python | ファイル変換処理 |

---

## 2. プロジェクト構成

```
MarkBridge/
├── App.xaml.cs              # アプリケーションエントリ
├── MauiProgram.cs           # DIコンテナ設定
├── Components/
│   ├── Layout/
│   │   └── MainLayout.razor # タブナビゲーション、ステータスバー
│   └── Pages/
│       ├── Convert.razor    # 変換タブ
│       ├── FilesEditor.razor # ファイル管理・エディタ
│       └── Settings.razor   # 設定タブ
├── Services/
│   ├── AppStateService.cs   # 状態管理、設定永続化
│   ├── PythonEnvironmentService.cs # Python/venv管理
│   └── ConversionService.cs # ファイル変換処理
├── Python/
│   ├── markitdown_wrapper.py
│   └── docling_wrapper.py
├── docs/                    # ドキュメント
└── wwwroot/
    ├── css/app.css          # カスタムスタイル
    └── index.html           # Bootstrap CDN読込
```

---

## 3. サービス層

### 3.1 AppStateService

グローバル状態管理と設定永続化。

```csharp
// 主要プロパティ
public string VirtualEnvPath { get; set; }
public string DefaultOutputPath { get; set; }
public int MaxConcurrency { get; set; }
public bool AutoSaveEnabled { get; set; }

// 永続化
public async Task InitializeAsync();  // 起動時ロード
public async Task SaveAsync();        // 設定保存
```

**設定ファイル:** `%LocalAppData%\MarkBridge\settings.json`

### 3.2 PythonEnvironmentService

Python Install Manager連携、venv管理。

```csharp
// Python Install Manager
public bool IsPyInstalled();
public List<PythonVersion> GetInstalledVersions();
public async Task InstallVersionAsync(string version);
public async Task UninstallVersionAsync(string version);

// venv管理
public bool IsVenvValid(string path);
public async Task CreateVenvAsync(string path, string pythonVersion);
public async Task DeleteVenvAsync(string path);

// ライブラリ管理
public async Task InstallPackageAsync(string package);
public async Task UninstallPackageAsync(string package);
public string GetPackageVersion(string package);
```

### 3.3 ConversionService

ファイル変換処理。

```csharp
public async Task<ConversionResult> ConvertFileAsync(
    string inputPath,
    string outputPath,
    ConversionEngine engine,
    ConversionOptions options,
    CancellationToken cancellationToken,
    Action<string> onProgress);
```

---

## 4. プラットフォーム固有連携

### 4.1 ドラッグ＆ドロップ

MAUI Blazor HybridではWebView2内でのHTML5 D&Dが機能しないため、ネイティブMAUI層で実装。

**実装アーキテクチャ:**

```
MainPage.xaml
├── Grid (DropGestureRecognizer)
│   ├── DragOver イベント → AcceptedOperation = Copy
│   └── Drop イベント → Windows PlatformArgs経由でファイルパス取得
└── BlazorWebView
    └── Blazorコンポーネント
        └── MainPage.OnFilesDropped イベント購読
```

**コード例 (MainPage.xaml.cs):**

```csharp
#if WINDOWS
using Windows.ApplicationModel.DataTransfer;
using Windows.Storage;
#endif

private async void OnDrop(object? sender, DropEventArgs e)
{
#if WINDOWS
    var args = e.PlatformArgs;
    if (args?.DragEventArgs?.DataView != null)
    {
        var dataView = args.DragEventArgs.DataView;
        if (dataView.Contains(StandardDataFormats.StorageItems))
        {
            var items = await dataView.GetStorageItemsAsync();
            foreach (var item in items)
            {
                if (item is StorageFile file)
                    DroppedFilePaths.Add(file.Path);
                else if (item is StorageFolder folder)
                    DroppedFilePaths.Add(folder.Path);
            }
        }
    }
#endif
    OnFilesDropped?.Invoke(DroppedFilePaths);
}
```

### 4.2 フォルダ選択ダイアログ

```csharp
[DllImport("shell32.dll")]
public static extern IntPtr SHBrowseForFolder(ref BROWSEINFO lpbi);
```

### 4.3 ウィンドウ制御

```csharp
[DllImport("user32.dll")]
static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, 
                                 int X, int Y, int cx, int cy, uint uFlags);
```

---

## 5. 並列処理アーキテクチャ

### 5.1 エンジン別独立キュー

```
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ MarkItDown     │  │ Docling (CPU)  │  │ Docling (GPU)  │
│ Queue          │  │ Queue          │  │ Queue          │
│ [MaxConcurrency]│ │ [MaxConcurrency]│ │ [1 recommended]│
└────────────────┘  └────────────────┘  └────────────────┘
```

### 5.2 同時実行制御

```csharp
var options = new ParallelOptions 
{ 
    MaxDegreeOfParallelism = maxConcurrency, 
    CancellationToken = token 
};

await Parallel.ForEachAsync(files, options, async (file, ct) =>
{
    await ProcessSingleFileAsync(file, ct);
});
```

---

## 6. 設定永続化

### 6.1 設定ファイル

**パス:** `%LocalAppData%\MarkBridge\settings.json`

```json
{
  "VirtualEnvPath": "C:\\Users\\xxx\\AppData\\Local\\MarkBridge\\.venv",
  "DefaultOutputPath": "C:\\Users\\xxx\\Documents\\MarkBridge\\Output",
  "MaxConcurrency": 3,
  "AutoSaveEnabled": true,
  "Language": "en",
  "Theme": "light",
  "ActivePythonVersion": "3.12"
}
```

### 6.2 変換履歴

**パス:** `%LocalAppData%\MarkBridge\conversion_history.json`

```json
{
  "history": [
    {
      "timestamp": "2024-12-23T10:30:00Z",
      "inputFile": "document.pdf",
      "outputFile": "document_it.md",
      "engine": "MarkItDown",
      "success": true,
      "elapsedMs": 1234
    }
  ]
}
```

---

## 7. システム要件

| 項目 | 要件 |
|------|------|
| OS | Windows 10 (19044.0+) / Windows 11 |
| .NET | .NET 8 Runtime |
| Python | 3.10以上（Python Install Manager経由） |
| GPU（オプション） | NVIDIA RTXシリーズ推奨 |

---

## 8. ビルド・デプロイ

### 8.1 開発ビルド

```powershell
dotnet build
dotnet run
```

### 8.2 リリースビルド

```powershell
dotnet publish -c Release -r win10-x64 --self-contained
```

### 8.3 Unpackagedモデル

```xml
<PropertyGroup>
    <WindowsPackageType>None</WindowsPackageType>
    <RuntimeIdentifier>win10-x64</RuntimeIdentifier>
</PropertyGroup>
```
