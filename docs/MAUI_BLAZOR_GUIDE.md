# .NET 8 MAUI Blazor Hybrid 開発ガイド

本ドキュメントは、.NET 8 / MAUI Blazor Hybrid (Windows) 開発で遭遇しやすい課題と解決策をまとめた**一般的な開発ガイド**です。

> **Note:** MarkBridge固有の実装詳細は [ARCHITECTURE.md](ARCHITECTURE.md) および [PYTHON_ENVIRONMENT.md](PYTHON_ENVIRONMENT.md) を参照してください。

---

## 1. プロジェクト構成

### 1.1 Unpackaged モデル（推奨）

Windows向けデスクトップアプリを従来の `.exe` 形式で配布する場合、Unpackaged モデルを使用します。

```xml
<PropertyGroup>
    <TargetFramework>net8.0-windows10.0.19041.0</TargetFramework>
    <RuntimeIdentifier>win10-x64</RuntimeIdentifier>
    <WindowsPackageType>None</WindowsPackageType>
    <SelfContained>false</SelfContained>
</PropertyGroup>
```

### 1.2 UI Automation API の有効化

`System.Windows.Automation` を使用するには、FrameworkReference が必要です。

```xml
<ItemGroup Condition="$([MSBuild]::IsOSPlatform('Windows'))">
    <FrameworkReference Include="Microsoft.WindowsDesktop.App" />
</ItemGroup>
```

### 1.3 launchSettings.json

`dotnet run` でデバッグ実行するためのプロファイル設定：

```json
{
  "profiles": {
    "Windows Machine": {
      "commandName": "Project",
      "launchBrowser": false
    }
  }
}
```

---

## 2. スレッディング

### 2.1 基本原則

Blazor UIスレッドをブロックしないため、重い処理は必ずバックグラウンドで実行します。

```csharp
// ❌ 悪い例：UIスレッドをブロック
var result = HeavyOperation();

// ✅ 良い例：バックグラウンド実行
var result = await Task.Run(() => HeavyOperation());

// UI更新はInvokeAsyncで
await InvokeAsync(() => StateHasChanged());
```

### 2.2 UI Automation 操作

UI Automation API はUIスレッドで動作できますが、処理時間が長い場合はバックグラウンドで実行：

```csharp
await Task.Run(async () => {
    // UI Automation 操作
    var element = AutomationElement.FromHandle(hwnd);
    // ...
});
```

---

## 3. WebView2 と Blazor の制限

### 3.1 ネイティブ `<select>` 要素の問題

**問題**: WebView2 上の `<select>` ドロップダウンは、ウィンドウ移動時に正しく追従しない。

**解決策**: HTML/CSS でカスタムドロップダウンを実装：

```razor
<div style="position: relative;">
    <div class="form-control" @onclick="ToggleDropdown">
        @SelectedText ▼
    </div>
    
    @if(IsOpen)
    {
        <div style="position: absolute; top: 100%; left: 0; right: 0; z-index: 100;">
            @foreach(var item in Items)
            {
                <div @onclick="() => Select(item)">@item.Name</div>
            }
        </div>
        
        <!-- クリックで閉じるための透明背景 -->
        <div style="position: fixed; inset: 0; z-index: 99;" 
             @onclick="() => IsOpen = false"></div>
    }
</div>
```

### 3.2 ネイティブツールチップ

**問題**: `title` 属性のツールチップがウィンドウ移動時に元の位置に残る。

**対応**: 軽微な問題として許容するか、カスタムツールチップを実装。

---

## 4. キーボードイベント

### 4.1 モーダルでのキーボード操作

**問題**: モーダルダイアログでキーボードイベントが発火しない。

**解決策**:

1. ルート要素に `tabindex="-1"` を設定
2. `@ref` で `ElementReference` を取得
3. 表示後に `FocusAsync()` でフォーカス設定

```razor
<div class="modal" tabindex="-1" @ref="ModalRef" @onkeydown="OnKeyDown">
    <!-- モーダル内容 -->
</div>

@code {
    private ElementReference ModalRef;
    
    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        if(firstRender && ShowModal)
        {
            await ModalRef.FocusAsync();
        }
    }
    
    private void OnKeyDown(KeyboardEventArgs e)
    {
        switch(e.Key)
        {
            case "Escape": CloseModal(); break;
            case "Enter": Confirm(); break;
        }
    }
}
```

---

## 5. Win32 API 連携

### 5.1 ウィンドウ境界の取得 (DWM)

**問題**: `GetWindowRect` は不可視のウィンドウ枠（影）を含む。

**解決策**: `DwmGetWindowAttribute` で実際の描画領域を取得：

```csharp
[DllImport("dwmapi.dll")]
static extern int DwmGetWindowAttribute(IntPtr hwnd, int dwAttribute, out RECT rect, int cbSize);

const int DWMWA_EXTENDED_FRAME_BOUNDS = 9;

public static RECT GetActualWindowRect(IntPtr hwnd)
{
    if (DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, out RECT rect, Marshal.SizeOf<RECT>()) == 0)
    {
        return rect;
    }
    // フォールバック
    GetWindowRect(hwnd, out rect);
    return rect;
}
```

### 5.2 Always on Top

```csharp
[DllImport("user32.dll")]
static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

static readonly IntPtr HWND_TOPMOST = new(-1);
static readonly IntPtr HWND_NOTOPMOST = new(-2);
const uint SWP_NOMOVE = 0x0002;
const uint SWP_NOSIZE = 0x0001;

public static void SetAlwaysOnTop(IntPtr hwnd, bool enable)
{
    SetWindowPos(hwnd, enable ? HWND_TOPMOST : HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE);
}
```

### 5.3 バックグラウンドでのキー送信

ウィンドウをアクティブ化せずにキーストロークを送信：

```csharp
[DllImport("user32.dll")]
static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

const uint WM_KEYDOWN = 0x0100;
const uint WM_KEYUP = 0x0101;

public static void SendKeyBackground(IntPtr hwnd, int vkCode)
{
    PostMessage(hwnd, WM_KEYDOWN, (IntPtr)vkCode, IntPtr.Zero);
    PostMessage(hwnd, WM_KEYUP, (IntPtr)vkCode, IntPtr.Zero);
}
```

---

## 6. ウィンドウ状態の永続化

### 6.1 競合状態の回避

**問題**: 起動時の復元処理中に `SizeChanged` が発火し、不完全なサイズで上書き保存される。

**解決策**:

```csharp
private bool _isRestoring = true;
private Timer? _debounceTimer;

private void OnSizeChanged(object? sender, EventArgs e)
{
    // 復元中は無視
    if (_isRestoring) return;
    
    // 極端に小さいサイズは無視（最小化時など）
    if (Width < 100 || Height < 100) return;
    
    // デバウンス処理
    _debounceTimer?.Dispose();
    _debounceTimer = new Timer(async _ => {
        await SaveWindowState();
    }, null, 500, Timeout.Infinite);
}

private async Task RestoreWindowState()
{
    _isRestoring = true;
    try
    {
        // ウィンドウ位置・サイズを復元
        // ...
    }
    finally
    {
        await Task.Delay(200); // 安定化待機
        _isRestoring = false;
    }
}
```

---

## 7. SkiaSharp メモリ管理

### 7.1 基本ルール

`SKBitmap`, `SKImage`, `SKCanvas`, `SKPaint` などはアンマネージドメモリを使用。明示的な `Dispose()` が必須。

```csharp
// ✅ 良い例：using ステートメント
using var bitmap = new SKBitmap(width, height);
using var canvas = new SKCanvas(bitmap);
using var paint = new SKPaint();

// ✅ 良い例：try-finally
SKBitmap? result = null;
try
{
    result = ProcessImage(source);
    return result;
}
catch
{
    result?.Dispose();
    throw;
}
```

### 7.2 画像処理ループでの注意

```csharp
// ❌ 悪い例：中間オブジェクトがリーク
foreach(var page in pages)
{
    var processed = Process(page.Image); // previous `processed` is leaked!
    results.Add(processed);
}

// ✅ 良い例：明示的に管理
foreach(var page in pages)
{
    var processed = Process(page.Image);
    results.Add(processed);
    // 元画像が不要な場合は破棄
    // page.Image.Dispose();
}
```

---

## 8. Blazor コンポーネント パターン

### 8.1 状態変更の通知

```csharp
// AppStateService.cs
public class AppStateService
{
    public event Action? OnChange;
    
    public void NotifyStateChanged() => OnChange?.Invoke();
}

// Component.razor
@inject AppStateService AppState
@implements IDisposable

@code {
    protected override void OnInitialized()
    {
        AppState.OnChange += StateHasChanged;
    }
    
    public void Dispose()
    {
        AppState.OnChange -= StateHasChanged;
    }
}
```

### 8.2 非同期初期化

```csharp
protected override async Task OnInitializedAsync()
{
    // 非同期で初期データを読み込み
    await LoadDataAsync();
}

protected override async Task OnAfterRenderAsync(bool firstRender)
{
    if (firstRender)
    {
        // DOM操作やJSInteropはここで
        await JSRuntime.InvokeVoidAsync("initialize");
    }
}
```

---

## 9. 設定の永続化

### 9.1 JSON シリアライズ

```csharp
public class SettingsStorageService
{
    private readonly string _filePath;
    
    public SettingsStorageService()
    {
        var appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var appFolder = Path.Combine(appData, "YourAppName");
        Directory.CreateDirectory(appFolder);
        _filePath = Path.Combine(appFolder, "settings.json");
    }
    
    public async Task<T?> LoadAsync<T>() where T : class
    {
        if (!File.Exists(_filePath)) return null;
        
        var json = await File.ReadAllTextAsync(_filePath);
        return JsonSerializer.Deserialize<T>(json);
    }
    
    public async Task SaveAsync<T>(T settings)
    {
        var json = JsonSerializer.Serialize(settings, new JsonSerializerOptions { WriteIndented = true });
        await File.WriteAllTextAsync(_filePath, json);
    }
}
```

---

## 10. トラブルシューティング

### よくある問題と解決策

| 問題 | 原因 | 解決策 |
|------|------|--------|
| UIがフリーズする | 重い処理をUIスレッドで実行 | `Task.Run()` でバックグラウンド実行 |
| ドロップダウンがずれる | WebView2の`<select>`バグ | カスタムドロップダウン実装 |
| キーイベントが発火しない | フォーカスがない | `tabindex` + `FocusAsync()` |
| メモリリーク | SkiaSharpオブジェクト未解放 | `using` または明示的 `Dispose()` |
| 設定が保存されない | 起動時の競合状態 | デバウンス + ガード条件 |
| JavaFXアプリからテキスト取得不可 | Win32 API の制限 | UI Automation API を使用 |
| インストール後に画面が真っ白 | Program Files権限問題 | 環境変数 `WEBVIEW2_USER_DATA_FOLDER` を設定 |

---

## 18. 配布・インストーラ作成時の注意

### 18.1 "Program Files" インストール時の白画面 (White Screen of Death)

**問題**:
インストーラで `Program Files` などのシステムフォルダにインストールすると、起動時に画面が真っ白のまま何も表示されない。

**原因**:
WebView2 ランタイムはデフォルトで実行ファイルと同じディレクトリに `Example.exe.WebView2` というユーザーデータフォルダ（キャッシュ等）を作成しようとする。`Program Files` は書き込み権限が制限されているため、このフォルダ作成に失敗し、WebView2 がクラッシュする。

**解決策**:
環境変数 `WEBVIEW2_USER_DATA_FOLDER` を設定し、書き込み可能な場所（LocalAppDataなど）を明示的に指定する。これは **`InitializeComponent()` 呼び出しの前** に行う必要がある。

**`App.xaml.cs` (WinUI)**:
```csharp
public App()
{
    // Program Files インストール時の白画面対策
    var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
    var cacheFolder = Path.Combine(localAppData, "YourAppName", "WebView2");
    
    // フォルダは自動生成されるが、親ディレクトリ権限確保のため構成
    Environment.SetEnvironmentVariable("WEBVIEW2_USER_DATA_FOLDER", cacheFolder);

    this.InitializeComponent();
}
```

### 18.2 インストーラ (Inno Setup)

自己完結型 (Self-Contained) としてビルドした出力を配布する場合のスクリプト例。

**ビルドコマンド**:
```powershell
dotnet publish -c Release --self-contained true
```

**[Inno Setup Script](file:///c:/git/ReaderCapture2/installer/setup.iss)**
```pascal
[Setup]
AppName=MyApp
DefaultDirName={autopf}\MyApp
...

[Files]
Source: "..\bin\Release\net8.0-windows10.0.19041.0\win10-x64\publish\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
```

---

---

## 11. スクリーンキャプチャ

### 11.1 キャプチャ方式の比較

| 方式 | メリット | デメリット |
|------|----------|------------|
| **PrintWindow API** | バックグラウンドキャプチャ可能、ちらつきなし | 一部アプリで黒画像になる可能性 |
| **CopyFromScreen** | 確実に動作 | 自アプリを隠す必要あり、ちらつき発生 |

### 11.2 PrintWindow 実装

```csharp
[DllImport("user32.dll")]
static extern bool PrintWindow(IntPtr hwnd, IntPtr hdcBlt, uint nFlags);

const uint PW_RENDERFULLCONTENT = 0x00000002;

public static Bitmap CaptureWithPrintWindow(IntPtr hwnd, RECT rect)
{
    int width = rect.Right - rect.Left;
    int height = rect.Bottom - rect.Top;
    
    var bmp = new Bitmap(width, height, PixelFormat.Format32bppArgb);
    using (var g = Graphics.FromImage(bmp))
    {
        IntPtr hdc = g.GetHdc();
        try
        {
            PrintWindow(hwnd, hdc, PW_RENDERFULLCONTENT);
        }
        finally
        {
            g.ReleaseHdc(hdc);
        }
    }
    return bmp;
}
```

### 11.3 CopyFromScreen フォールバック

```csharp
public static Bitmap CaptureWithScreen(RECT rect)
{
    int width = rect.Right - rect.Left;
    int height = rect.Bottom - rect.Top;
    
    var bmp = new Bitmap(width, height);
    using (var g = Graphics.FromImage(bmp))
    {
        g.CopyFromScreen(rect.Left, rect.Top, 0, 0, new Size(width, height));
    }
    return bmp;
}
```

### 11.4 自アプリの表示制御

Screen方式使用時は自アプリを一時的に隠す：

```csharp
// キャプチャ前
WindowService.HideSelf();
await Task.Delay(200); // 描画完了を待機

// キャプチャ実行
var bmp = CaptureWithScreen(rect);

// 終了後
WindowService.ShowSelf();
```

---

## 12. JavaFX アプリケーション操作（Kindle等）

### 12.1 UI Automation でのテキスト取得

JavaFXアプリは Win32 API (GetWindowText, EnumChildWindows) でテキスト取得不可。UI Automation を使用：

```csharp
public static List<string> GetAllTextFromWindow(IntPtr hwnd)
{
    var texts = new List<string>();
    var element = AutomationElement.FromHandle(hwnd);
    
    var allElements = element.FindAll(TreeScope.Descendants, Condition.TrueCondition);
    
    foreach (AutomationElement el in allElements)
    {
        // 1. Name プロパティ
        if (!string.IsNullOrEmpty(el.Current.Name))
            texts.Add(el.Current.Name);
        
        // 2. ValuePattern
        if (el.TryGetCurrentPattern(ValuePattern.Pattern, out object pattern))
        {
            var vp = (ValuePattern)pattern;
            if (!string.IsNullOrEmpty(vp.Current.Value))
                texts.Add(vp.Current.Value);
        }
        
        // 3. TextPattern
        if (el.TryGetCurrentPattern(TextPattern.Pattern, out pattern))
        {
            var tp = (TextPattern)pattern;
            texts.Add(tp.DocumentRange.GetText(-1));
        }
    }
    
    return texts;
}
```

### 12.2 Ctrl+G ダイアログ経由のページ移動

Kindle では `Ctrl+Home`/`Ctrl+End` が効かないため、ダイアログ経由で移動：

```csharp
public async Task GoToPage(int pageNumber)
{
    // 1. Ctrl+G でダイアログを開く
    SendKeyWithModifier(VK_G, VK_CONTROL);
    await Task.Delay(500);
    
    // 2. ページ番号を入力
    foreach (char c in pageNumber.ToString())
    {
        SendKey((byte)c);
        await Task.Delay(50);
    }
    
    // 3. Enter で確定
    SendKey(VK_RETURN);
}

public async Task<int?> DetectTotalPages()
{
    // 1. Ctrl+G でダイアログを開く
    SendKeyWithModifier(VK_G, VK_CONTROL);
    await Task.Delay(500);
    
    // 2. UI Automation でテキスト収集
    var texts = GetAllTextFromWindow(GetForegroundWindow());
    
    // 3. "/42" のようなパターンを検索
    var regex = new Regex(@"/(\d+)");
    foreach (var text in texts)
    {
        var match = regex.Match(text);
        if (match.Success)
        {
            // 4. Escape でダイアログを閉じる
            SendKey(VK_ESCAPE);
            return int.Parse(match.Groups[1].Value);
        }
    }
    
    SendKey(VK_ESCAPE);
    return null;
}
```

---

## 13. QuestPDF での PDF 生成

### 13.1 動的ページサイズ

画像サイズに合わせたページを生成：

```csharp
using QuestPDF.Fluent;
using QuestPDF.Infrastructure;

public async Task ExportPdf(IEnumerable<CapturedPage> pages, string outputPath)
{
    QuestPDF.Settings.License = LicenseType.Community;
    
    await Task.Run(() => {
        Document.Create(container => {
            foreach (var page in pages)
            {
                if (page.Image == null) continue;
                
                container.Page(p => {
                    // 画像サイズをページサイズに設定
                    p.Size(new PageSize(page.Image.Width, page.Image.Height));
                    p.Margin(0);
                    
                    p.Content().Element(e => {
                        using var img = SKImage.FromBitmap(page.Image);
                        using var data = img.Encode(SKEncodedImageFormat.Jpeg, 85);
                        e.Image(data.ToArray()).FitArea();
                    });
                });
            }
        })
        .GeneratePdf(outputPath);
    });
}
```

---

## 14. 画像重複検出

### 14.1 サンプリング比較アルゴリズム

全ピクセル比較は遅すぎるため、ランダムサンプリングで高速化：

```csharp
public bool AreBitmapsSimilar(SKBitmap bmp1, SKBitmap bmp2, double thresholdPercent)
{
    // サイズチェック
    if (bmp1.Width != bmp2.Width || bmp1.Height != bmp2.Height)
        return false;
    
    const int sampleSize = 100;
    int matchingPixels = 0;
    var random = new Random(42); // 固定シードで再現性確保
    
    for (int i = 0; i < sampleSize; i++)
    {
        int x = random.Next(bmp1.Width);
        int y = random.Next(bmp1.Height);
        
        var p1 = bmp1.GetPixel(x, y);
        var p2 = bmp2.GetPixel(x, y);
        
        // RGB各チャンネルで±5の許容差
        if (Math.Abs(p1.Red - p2.Red) <= 5 &&
            Math.Abs(p1.Green - p2.Green) <= 5 &&
            Math.Abs(p1.Blue - p2.Blue) <= 5)
        {
            matchingPixels++;
        }
    }
    
    double matchPercent = (double)matchingPixels / sampleSize * 100;
    return matchPercent >= (100 - thresholdPercent);
}
```

---

## 15. Gallery 後処理パターン

### 15.1 選択アイテムの一括処理

複数選択したアイテムを処理し、リストを更新：

```csharp
private void ProcessSelected(Func<SKBitmap, List<SKBitmap>> processor)
{
    var selected = AppState.CapturedPages.Where(p => p.IsSelected).ToList();
    
    foreach (var page in selected)
    {
        if (page.Image == null) continue;
        
        var index = AppState.CapturedPages.IndexOf(page);
        var results = processor(page.Image);
        
        // 元のアイテムを削除
        AppState.CapturedPages.Remove(page);
        page.Dispose();
        
        // 結果を挿入（逆順で挿入して順序を維持）
        for (int i = results.Count - 1; i >= 0; i--)
        {
            var newPage = new CapturedPage { 
                Image = results[i], 
                PageNumber = page.PageNumber 
            };
            AppState.CapturedPages.Insert(index, newPage);
        }
    }
    
    AppState.NotifyStateChanged();
}
```

### 15.2 Shift + クリック による範囲選択

```csharp
private int lastClickedIndex = -1;

private void HandleItemClick(CapturedPage page, MouseEventArgs e)
{
    var currentIndex = Pages.IndexOf(page);
    
    if (e.ShiftKey && lastClickedIndex >= 0)
    {
        // 範囲選択
        int start = Math.Min(lastClickedIndex, currentIndex);
        int end = Math.Max(lastClickedIndex, currentIndex);
        
        for (int i = start; i <= end; i++)
        {
            Pages[i].IsSelected = true;
        }
    }
    else
    {
        // 通常の選択切り替え
        page.IsSelected = !page.IsSelected;
        lastClickedIndex = currentIndex;
    }
    
    StateHasChanged();
}
```

---

## 16. Base64 画像表示

### 16.1 Blazor での画像表示

Blazorコンポーネントで SkiaSharp 画像を表示する場合、Base64 エンコードを使用：

```csharp
private string GetImageSource(SKBitmap bitmap)
{
    if (bitmap == null) return "";
    
    try
    {
        using var image = SKImage.FromBitmap(bitmap);
        using var data = image.Encode(SKEncodedImageFormat.Jpeg, 70);
        
        var base64 = Convert.ToBase64String(data.ToArray());
        return $"data:image/jpeg;base64,{base64}";
    }
    catch
    {
        return "";
    }
}
```

```razor
<img src="@GetImageSource(page.Image)" />
```

**注意**: 大量の画像を表示する場合、毎回エンコードするとパフォーマンスに影響。キャッシュを検討。

---

## 17. サービス間の依存関係注入

### 17.1 ExportService での AppStateService 参照

設定値をサービスで使用する場合、コンストラクタ注入：

```csharp
public class ExportService
{
    private readonly AppStateService _appState;
    
    public ExportService(AppStateService appState)
    {
        _appState = appState;
    }
    
    public async Task Export(...)
    {
        // 設定値を参照
        int quality = _appState.Settings.JpegQuality;
        // ...
    }
}
```

### 17.2 MauiProgram.cs での登録

```csharp
builder.Services.AddSingleton<AppStateService>();
builder.Services.AddSingleton<SettingsStorageService>();
builder.Services.AddSingleton<ExportService>();
builder.Services.AddSingleton<CaptureService>();
builder.Services.AddSingleton<ImageProcessingService>();
```

---

## 18. App.xaml.cs での ウィンドウ状態保存（推奨パターン）

### 18.1 CreateWindow オーバーライド

**問題**: `MauiProgram.cs` の `ConfigureLifecycleEvents` でウィンドウ状態を復元すると、白い画面になることがある。

**解決策**: `App.xaml.cs` で `CreateWindow` をオーバーライドし、`window.Created`/`SizeChanged`/`Stopped` イベントを使用：

```csharp
public partial class App : Application
{
    private readonly SettingsStorageService _storageService;
    private readonly AppStateService _appState;

    public App(SettingsStorageService storageService, AppStateService appState)
    {
        _storageService = storageService;
        _appState = appState;
        InitializeComponent();
        MainPage = new MainPage();
    }

    protected override Window CreateWindow(IActivationState? activationState)
    {
        var window = base.CreateWindow(activationState);
        bool isRestoring = true;

        // 復元
        window.Created += async (s, e) =>
        {
            try 
            {
                var settings = await _storageService.LoadAsync();
                if (settings.WindowWidth >= 100 && settings.WindowHeight >= 100)
                {
                    window.X = settings.WindowX;
                    window.Y = settings.WindowY;
                    window.Width = settings.WindowWidth;
                    window.Height = settings.WindowHeight;
                }
            } 
            finally 
            {
                await Task.Delay(1000); // 安定化待機
                isRestoring = false;
            }
        };
        
        // デバウンス保存
        IDispatcherTimer? debounceTimer = null;
        void TriggerSave()
        {
            if (isRestoring) return;
            debounceTimer ??= Application.Current?.Dispatcher.CreateTimer();
            if (debounceTimer != null) 
            {
                debounceTimer.Interval = TimeSpan.FromMilliseconds(500);
                debounceTimer.Tick += (s, e) => { SaveBounds(window); debounceTimer.Stop(); };
            }
            debounceTimer?.Stop();
            debounceTimer?.Start();
        }

        window.SizeChanged += (s, e) => TriggerSave();
        window.Stopped += (s, e) => SaveBounds(window); // 終了時に強制保存
        
        return window;
    }

    private void SaveBounds(Window window)
    {
        if (window.Width >= 100 && window.Height >= 100)
        {
            _appState.Settings.WindowX = window.X;
            _appState.Settings.WindowY = window.Y;
            _appState.Settings.WindowWidth = window.Width;
            _appState.Settings.WindowHeight = window.Height;
            _ = _appState.SaveSettingsAsync();
        }
    }
}
```

### 18.2 重要なポイント

- **DIコンストラクタ**: `SettingsStorageService` と `AppStateService` をコンストラクタ注入
- **isRestoring フラグ**: 復元中の保存を防止
- **Task.Delay(1000)**: ウィンドウ安定化待機（短すぎると競合状態）
- **サイズ100未満は無視**: 最小化時の異常値を保存しない

---

## 19. 外部プロセス（pip等）のハング対策

### 19.1 問題

`pip install` 等の外部プロセスで `StandardOutput.ReadToEndAsync()` を使用すると、出力がフラッシュされないためプロセスがハングする。

### 19.2 解決策：行単位読み取り + タイムアウト

```csharp
public async Task<bool> InstallPackageAsync(string packageName, string pipPath)
{
    var psi = new ProcessStartInfo
    {
        FileName = pipPath,
        Arguments = $"install {packageName}",
        RedirectStandardOutput = true,
        RedirectStandardError = true,
        UseShellExecute = false,
        CreateNoWindow = true
    };
    
    using var process = Process.Start(psi);
    if (process == null) return false;
    
    var outputLines = new List<string>();
    var readTask = Task.Run(async () =>
    {
        while (!process.StandardOutput.EndOfStream)
        {
            var line = await process.StandardOutput.ReadLineAsync();
            if (!string.IsNullOrEmpty(line))
            {
                outputLines.Add(line);
                // UIに進捗を通知（オプション）
                _appState.LastLogLine = line.Length > 60 ? line[..60] + "..." : line;
                _appState.InstallProgress = Math.Min(95, outputLines.Count * 2);
            }
        }
    });
    
    // タイムアウト付きで待機
    using var cts = new CancellationTokenSource(TimeSpan.FromMinutes(5));
    try
    {
        await process.WaitForExitAsync(cts.Token);
        await readTask;
    }
    catch (OperationCanceledException)
    {
        process.Kill();
        return false;
    }
    
    return process.ExitCode == 0;
}
```

### 19.3 重要なポイント

- **ReadLineAsync**: 行単位で読み取ることでバッファフラッシュ問題を回避
- **Task.Run**: 読み取りをバックグラウンドで実行
- **CancellationTokenSource**: タイムアウトでハング防止
- **process.Kill()**: タイムアウト時はプロセスを強制終了

---

## 20. 設定ファイルのバリデーションとリカバリ

### 20.1 問題

不正な設定値（ウィンドウサイズ0等）が保存されると、アプリが正常に起動しなくなる。

### 20.2 解決策：読み込み時のバリデーション

```csharp
public async Task<AppSettings> LoadAsync()
{
    try
    {
        if (!File.Exists(_settingsFilePath))
            return AppSettings.CreateDefault();
        
        var json = await File.ReadAllTextAsync(_settingsFilePath);
        var settings = JsonSerializer.Deserialize<AppSettings>(json);
        
        if (settings == null) return AppSettings.CreateDefault();
        
        // バリデーションとリカバリ
        var defaults = AppSettings.CreateDefault();
        bool needsSave = false;
        
        // ウィンドウサイズが不正な場合はデフォルト値に修正
        if (settings.WindowWidth < 100 || settings.WindowHeight < 100)
        {
            settings.WindowWidth = 1024;
            settings.WindowHeight = 768;
            needsSave = true;
        }
        
        // 必須パスが空の場合はデフォルト値に修正
        if (string.IsNullOrEmpty(settings.VirtualEnvPath))
        {
            settings.VirtualEnvPath = defaults.VirtualEnvPath;
            needsSave = true;
        }
        
        // 修正が必要な場合は保存
        if (needsSave) await SaveAsync(settings);
        
        return settings;
    }
    catch
    {
        return AppSettings.CreateDefault();
    }
}
```

### 20.3 重要なポイント

- **自動修復**: 不正な値をデフォルト値で上書き
- **needsSave フラグ**: 修正があった場合のみ保存
- **例外キャッチ**: ファイル破損時はデフォルト設定を返す

---

## 21. Python外部プロセス実行時のUnicodeエンコーディング問題

### 21.1 問題

Windows環境でPythonプロセスを実行し、`Process` クラスで標準出力を受け取る際、PythonコードがUnicode文字（例: `\u2022` ビュレットなど）を出力しようとすると `UnicodeEncodeError: 'cp932' codec can't encode character...` が発生してプロセスがクラッシュする場合がある。
これはWindowsのコンソール標準エンコーディング（cp932）がデフォルトで使用されるためである。

### 21.2 解決策：環境変数でのUTF-8強制

Pythonプロセス起動時に `PYTHONIOENCODING` 環境変数を `utf-8` に設定する。

```csharp
var psi = new ProcessStartInfo
{
    FileName = "python.exe",
    Arguments = "script.py",
    RedirectStandardOutput = true,
    RedirectStandardError = true,
    UseShellExecute = false,
    CreateNoWindow = true,
    // C#側の読み取り設定もUTF-8にする
    StandardOutputEncoding = System.Text.Encoding.UTF8,
    StandardErrorEncoding = System.Text.Encoding.UTF8
};

// これが重要：Python側の出力をUTF-8に強制する
psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";

using var process = Process.Start(psi);
// ...
```

### 21.3 重要なポイント

- **PYTHONIOENCODING**: Pythonの標準入出力のエンコーディングを決定する環境変数。これを設定しないと、OSのデフォルト（Windowsならcp932）が使われることが多い。
- **StandardOutputEncoding**: C#側がストリームを読み取る際のエンコーディング。両方をUTF-8に合わせることで、文字化けやクラッシュを防ぐことができる。

---

## 22. 設定の記録・ロードに関する重要留意事項

### 22.1 問題: アプリ再起動設定がリセットされる

**現象**:
設定画面で値を変更して「保存」したにも関わらず、アプリを再起動すると設定が初期値に戻ってしまう。`settings.json` を確認すると、アプリ終了時にデフォルト値で上書きされている。

**原因**:
アプリ起動時に `SettingsStorageService.LoadAsync()` を呼び出して、アプリの状態 (`AppState`) に反映させる処理が抜けている場合、アプリは「デフォルト値」で起動する。
その後、ウィンドウを閉じる際などに「現在の状態を保存」する処理が走ると、メモリ上のデフォルト値で `settings.json` が上書きされてしまう。

### 22.2 解決策: 起動ライフサイクルでの明示的なロード

`App.xaml.cs` の `CreateWindow` または `OnLaunched` イベント内で、ウィンドウが表示される前に必ず設定をロードし、`AppState` に適用する。

**悪い例 (App.xaml.cs)**:
```csharp
public App(AppStateService appState)
{
    // ここで初期化しても、非同期ロードが終わる前にメイン画面が表示される可能性がある
    InitializeComponent();
}
```

**良い例 (App.xaml.cs)**:
```csharp
protected override Window CreateWindow(IActivationState? activationState)
{
    var window = base.CreateWindow(activationState);

    // ウィンドウ作成イベントでロードを実行
    window.Created += async (s, e) =>
    {
        // 1. 設定ファイルからロード
        await _appState.InitializeAsync();
        
        // 2. ロードした設定をウィンドウ等に適用
        if (_appState.Settings.WindowWidth > 0)
        {
            window.Width = _appState.Settings.WindowWidth;
        }
    };
    
    return window;
}
```

### 22.3 チェックリスト

設定機能実装時は以下を確認すること：

1.  **ロード処理**: アプリ起動時（`Window.Created` 等）に `LoadAsync` が呼ばれているか？
2.  **初期化順序**: 画面が表示される前に設定値がメモリ（`AppState`）に展開されているか？
3.  **上書き防止**: 設定未ロードの状態で `SaveAsync` が呼ばれるパスがないか？（例：ウィンドウ復元中のサイズ変更イベントによる自動保存）

---

## 23. 【保存版】汎用的なファイル処理・外部プロセス実行パターン

外部CLIツール（FFmpeg, Python, ImageMagick等）を呼び出して大量のファイルを処理する場合の「鉄板パターン」です。この構成を守ることで、ハングアップやUIフリーズ、メモリリークを確実に回避できます。

### 23.1 外部プロセス実行クラス (ProcessRunner)

**目的**:
標準出力/エラー出力のバッファ詰まりによるデッドロック（ハング）を完全に防ぎ、かつ非同期で実行する。

```csharp
/// <summary>
/// 外部プロセスを安全に実行するためのヘルパー
/// </summary>
public static class ProcessRunner
{
    public static async Task<ProcessResult> RunAsync(string exePath, string arguments, Action<string>? onOutput = null, CancellationToken ct = default)
    {
        var psi = new ProcessStartInfo
        {
            FileName = exePath,
            Arguments = arguments,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
            // 文字化け防止対策
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8
        };
        
        // Python等でのバッファリング無効化
        psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";

        using var process = new Process { StartInfo = psi };
        
        var outputBuilder = new StringBuilder();
        var errorBuilder = new StringBuilder();

        // 1. イベントハンドラで非同期読み取り（デッドロック回避の要）
        process.OutputDataReceived += (s, e) => 
        {
            if (e.Data != null) 
            {
                outputBuilder.AppendLine(e.Data);
                onOutput?.Invoke(e.Data); // リアルタイム通知
            }
        };
        
        process.ErrorDataReceived += (s, e) => 
        {
            if (e.Data != null) errorBuilder.AppendLine(e.Data);
        };

        // 2. プロセス開始
        if (!process.Start()) throw new Exception("Failed to start process");

        // 3. 非同期読み取り開始
        process.BeginOutputReadLine();
        process.BeginErrorReadLine();

        // 4. 非同期待機（タイムアウトやキャンセル対応もここで行う）
        await process.WaitForExitAsync(ct).ConfigureAwait(false);

        return new ProcessResult(process.ExitCode, outputBuilder.ToString(), errorBuilder.ToString());
    }
}

public record ProcessResult(int ExitCode, string StandardOutput, string StandardError);
```

### 23.2 並列処理制御パターン (Semaphore / Parallel.ForEachAsync)

**目的**:
CPUやメモリを食いつぶさないように、同時実行数を制限しながら大量のファイルを処理する。

```csharp
public async Task ProcessFilesAsync(List<string> files, int maxConcurrency, CancellationToken token)
{
    var options = new ParallelOptions 
    { 
        MaxDegreeOfParallelism = maxConcurrency, 
        CancellationToken = token 
    };

    // Parallel.ForEachAsync (.NET 6+) 推奨
    await Parallel.ForEachAsync(files, options, async (file, ct) =>
    {
        try 
        {
            // UIスレッドをブロックしないようTask.Runでラップする場合もあり
            // ただしProcessRunnerが非同期ならそのままawaitでOK
            await ProcessSingleFileAsync(file, ct);
        }
        catch (Exception ex)
        {
            // 個別の失敗で全体を止めない
            Log($"Failed: {file} - {ex.Message}");
        }
    });
}
```

### 23.3 UI更新のマーシャリング (InvokeAsync)

**目的**:
バックグラウンド処理（スレッドプール）から安全にBlazor UIを更新する。

```csharp
// サービス（ViewModelなど）
public event Action<string> OnProgress;

// コンポーネント (Blazor)
protected override void OnInitialized()
{
    // ★重要: InvokeAsyncでラップしてUIスレッドに戻す
    MyService.OnProgress += async (msg) => 
    {
        await InvokeAsync(() => 
        {
            statusMessage = msg;
            StateHasChanged();
        });
    };
}
```

### まとめ
「重い外部コマンド処理」を行うときは、これら3つのパターン（**ProcessRunner**, **ParallelOptions**, **InvokeAsync**）をセットで適用するのが、.NET MAUI/Blazorアプリにおける「正解」です。

