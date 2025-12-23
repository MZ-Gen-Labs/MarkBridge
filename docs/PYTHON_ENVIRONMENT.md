# Python環境管理

MarkBridgeにおけるPython環境（Python Install Manager、仮想環境、ライブラリ）の管理仕様。

---

## 1. Python Install Manager

### 1.1 概要

Python Software Foundation公式のWindows向けPython管理ツール。
複数のPythonバージョンを統一的にインストール・管理できる。

**公式サイト:** https://www.python.org/downloads/

### 1.2 対応環境

| 項目 | 要件 |
|------|------|
| OS | Windows 10 (19044.0+) / Windows 11 |
| 管理可能バージョン | Python 3.5以降 |

### 1.3 コマンドリファレンス

| コマンド | 説明 |
|----------|------|
| `py --version` | Install Managerのバージョン確認 |
| `py list` | インストール済みバージョン一覧 |
| `py install 3.12` | バージョンインストール |
| `py uninstall 3.12` | バージョンアンインストール |
| `py -3.12 script.py` | 指定バージョンで実行 |

### 1.4 出力例

```
# py list
Installed Python versions:
  3.13.1    C:\Users\xxx\AppData\Local\Programs\Python\Python313\python.exe
 *3.12.4    C:\Users\xxx\AppData\Local\Programs\Python\Python312\python.exe
  3.11.9    C:\Users\xxx\AppData\Local\Programs\Python\Python311\python.exe
```

`*` がアクティブ（デフォルト）バージョン。

### 1.5 MarkBridgeでの検出

```csharp
var psi = new ProcessStartInfo
{
    FileName = "py",
    Arguments = "--version",
    RedirectStandardOutput = true,
    UseShellExecute = false,
    CreateNoWindow = true
};

using var process = Process.Start(psi);
await process.WaitForExitAsync();
bool isInstalled = process.ExitCode == 0;
```

---

## 2. 仮想環境（venv）

### 2.1 目的

システムPython環境を汚さず、アプリ専用の隔離された環境を構築。

### 2.2 デフォルトパス

```
%LocalAppData%\MarkBridge\.venv
```

### 2.3 作成コマンド

```csharp
// 選択されたPythonバージョンでvenv作成
var psi = new ProcessStartInfo
{
    FileName = "py",
    Arguments = $"-{selectedVersion} -m venv \"{venvPath}\"",
    UseShellExecute = false,
    CreateNoWindow = true
};
```

### 2.4 検証方法

```csharp
public bool IsVenvValid(string path)
{
    var pythonPath = Path.Combine(path, "Scripts", "python.exe");
    var pipPath = Path.Combine(path, "Scripts", "pip.exe");
    return File.Exists(pythonPath) && File.Exists(pipPath);
}
```

---

## 3. ライブラリ管理

### 3.1 対象ライブラリ

| ライブラリ | 説明 | pipコマンド |
|------------|------|-------------|
| MarkItDown | 標準変換エンジン | `pip install markitdown` |
| Docling | 高度PDF/OCR変換 | `pip install docling` |
| PyTorch (CUDA) | GPU変換用（通常版） | `pip install torch --index-url https://download.pytorch.org/whl/cu121` |
| PyTorch Nightly | GPU変換用（通常版で動作しない場合） | `pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cu128` |

### 3.2 排他制御

PyTorch (CUDA) と PyTorch Nightly は同時インストール不可。
片方インストール時は、もう片方のInstallボタンを非活性化。

### 3.3 バージョン確認

```csharp
public async Task<string?> GetPackageVersionAsync(string package)
{
    var psi = new ProcessStartInfo
    {
        FileName = GetVenvPipPath(),
        Arguments = $"show {package}",
        RedirectStandardOutput = true,
        UseShellExecute = false,
        CreateNoWindow = true
    };
    
    // 出力から "Version: X.X.X" を抽出
}
```

---

## 4. 変換プロセス

### 4.1 プロセス実行パターン

```csharp
var psi = new ProcessStartInfo
{
    FileName = pythonPath,
    Arguments = arguments,
    RedirectStandardOutput = true,
    RedirectStandardError = true,
    UseShellExecute = false,
    CreateNoWindow = true,
    StandardOutputEncoding = Encoding.UTF8,
    StandardErrorEncoding = Encoding.UTF8
};

// バッファリング無効化（デッドロック防止）
psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";
psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
```

### 4.2 デッドロック防止

**問題:** `WaitForExit()` 前に出力を読まないとパイプバッファが埋まりデッドロック。

**解決策:**
```csharp
process.OutputDataReceived += (s, e) =>
{
    if (e.Data != null)
    {
        output.AppendLine(e.Data);
        onProgress?.Invoke(e.Data);
    }
};

process.Start();
process.BeginOutputReadLine();
process.BeginErrorReadLine();
await process.WaitForExitAsync(cancellationToken);
```

### 4.3 UIスレッドマーシャリング

**問題:** バックグラウンドスレッドから直接UI更新するとクラッシュ。

**解決策:**
```csharp
// Blazorコンポーネントでの安全なイベント購読
private Action _handler;
protected override void OnInitialized()
{
    _handler = async () => await InvokeAsync(StateHasChanged);
    AppState.OnChange += _handler;
}
```

---

## 5. トラブルシューティング

| 問題 | 原因 | 解決策 |
|------|------|--------|
| `py` コマンドが見つからない | Install Manager未インストール | python.org からインストール |
| venv作成失敗 | Pythonバージョン未選択 | アクティブバージョンを設定 |
| pip installハング | 出力バッファ詰まり | PYTHONUNBUFFERED=1 設定 |
| 変換中UIフリーズ | UIスレッドブロック | Task.Run + InvokeAsync |
| 文字化け | エンコーディング不一致 | PYTHONIOENCODING=utf-8 |
