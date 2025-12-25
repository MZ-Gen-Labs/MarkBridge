using System.Text.Json;

namespace MarkBridge.Services;

/// <summary>
/// Application state service - manages global state and settings persistence
/// </summary>
public class AppStateService
{
    private readonly string _settingsFilePath;
    private AppSettings _settings = new();
    private bool _isInitialized;

    public event Action? OnChange;

    public AppStateService()
    {
        var appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var appFolder = Path.Combine(appData, "MarkBridge");
        Directory.CreateDirectory(appFolder);
        _settingsFilePath = Path.Combine(appFolder, "settings.json");
    }

    #region Properties

    public string SystemPythonPath
    {
        get => _settings.SystemPythonPath;
        set { _settings.SystemPythonPath = value; NotifyStateChanged(); }
    }

    public string VirtualEnvPath
    {
        get => _settings.VirtualEnvPath;
        set { _settings.VirtualEnvPath = value; NotifyStateChanged(); }
    }

    public string DefaultOutputPath
    {
        get => _settings.DefaultOutputPath;
        set { _settings.DefaultOutputPath = value; NotifyStateChanged(); }
    }

    public bool UseOriginalFolderForOutput
    {
        get => _settings.UseOriginalFolderForOutput;
        set { _settings.UseOriginalFolderForOutput = value; NotifyStateChanged(); }
    }

    public bool AutoSaveEnabled
    {
        get => _settings.AutoSaveEnabled;
        set { _settings.AutoSaveEnabled = value; NotifyStateChanged(); }
    }

    public string Language
    {
        get => _settings.Language;
        set { _settings.Language = value; NotifyStateChanged(); }
    }

    public string Theme
    {
        get => _settings.Theme;
        set { _settings.Theme = value; NotifyStateChanged(); }
    }

    public int MaxConcurrency
    {
        get => _settings.MaxConcurrency;
        set { _settings.MaxConcurrency = value; NotifyStateChanged(); }
    }

    public ConversionEngine SelectedEngine
    {
        get => _settings.SelectedEngine;
        set { _settings.SelectedEngine = value; NotifyStateChanged(); }
    }

    public bool EnableOcr
    {
        get => _settings.EnableOcr;
        set { _settings.EnableOcr = value; NotifyStateChanged(); }
    }

    public bool ForceFullPageOcr
    {
        get => _settings.ForceFullPageOcr;
        set { _settings.ForceFullPageOcr = value; NotifyStateChanged(); }
    }

    public ImageExportMode ImageExportMode
    {
        get => _settings.ImageExportMode;
        set { _settings.ImageExportMode = value; NotifyStateChanged(); }
    }

    public bool UseMarkItDown
    {
        get => _settings.UseMarkItDown;
        set { _settings.UseMarkItDown = value; NotifyStateChanged(); }
    }

    public bool UseDocling
    {
        get => _settings.UseDocling;
        set { _settings.UseDocling = value; NotifyStateChanged(); }
    }

    public bool UseDoclingGpu
    {
        get => _settings.UseDoclingGpu;
        set { _settings.UseDoclingGpu = value; NotifyStateChanged(); }
    }

    public bool UsePaddleOcr
    {
        get => _settings.UsePaddleOcr;
        set { _settings.UsePaddleOcr = value; NotifyStateChanged(); }
    }

    public bool UsePaddleOcrGpu
    {
        get => _settings.UsePaddleOcrGpu;
        set { _settings.UsePaddleOcrGpu = value; NotifyStateChanged(); }
    }

    #endregion

    #region Status

    public string StatusMessage { get; private set; } = "Ready";
    public bool IsProcessing { get; private set; }
    public bool IsVenvActive { get; set; }
    public string? PythonVersion { get; set; }
    public string? MarkItDownVersion { get; set; }
    public string? DoclingVersion { get; set; }

    public void SetStatus(string message, bool isProcessing = false)
    {
        StatusMessage = message;
        IsProcessing = isProcessing;
        NotifyStateChanged();
    }

    #endregion

    #region Conversion Queue (in-memory only, not persisted)

    /// <summary>
    /// Conversion queue items - kept in memory across tab switches but not saved to disk
    /// </summary>
    public List<QueueItem> QueueItems { get; } = new();

    #endregion

    #region Editor State (in-memory only, not persisted)

    /// <summary>
    /// Currently open file path in the editor
    /// </summary>
    public string? EditorOpenFilePath { get; set; }

    /// <summary>
    /// Current editor content (for unsaved changes)
    /// </summary>
    public string EditorContent { get; set; } = string.Empty;

    /// <summary>
    /// Original content when file was loaded (to detect changes)
    /// </summary>
    public string EditorOriginalContent { get; set; } = string.Empty;

    /// <summary>
    /// Current directory path in the file explorer
    /// </summary>
    public string EditorCurrentPath { get; set; } = string.Empty;

    #endregion

    #region Persistence

    public async Task InitializeAsync()
    {
        if (_isInitialized) return;

        try
        {
            if (File.Exists(_settingsFilePath))
            {
                var json = await File.ReadAllTextAsync(_settingsFilePath);
                var loaded = JsonSerializer.Deserialize<AppSettings>(json);
                if (loaded != null)
                {
                    _settings = loaded;
                }
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"Failed to load settings: {ex.Message}");
        }

        // Apply defaults if needed
        if (string.IsNullOrEmpty(_settings.DefaultOutputPath))
        {
            var documents = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
            _settings.DefaultOutputPath = Path.Combine(documents, "MarkBridge", "Output");
        }

        if (string.IsNullOrEmpty(_settings.VirtualEnvPath))
        {
            var appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            _settings.VirtualEnvPath = Path.Combine(appData, "MarkBridge", ".venv");
        }

        _isInitialized = true;
        NotifyStateChanged();
    }

    public async Task SaveAsync()
    {
        try
        {
            var json = JsonSerializer.Serialize(_settings, new JsonSerializerOptions { WriteIndented = true });
            await File.WriteAllTextAsync(_settingsFilePath, json);
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"Failed to save settings: {ex.Message}");
        }
    }

    #endregion

    public void NotifyStateChanged()
    {
        OnChange?.Invoke();
        _ = SaveAsync(); // Auto-save on change
    }
}

public class AppSettings
{
    public string SystemPythonPath { get; set; } = string.Empty;
    public string VirtualEnvPath { get; set; } = string.Empty;
    public string DefaultOutputPath { get; set; } = string.Empty;
    public bool UseOriginalFolderForOutput { get; set; } = true;
    public bool AutoSaveEnabled { get; set; } = true;
    public string Language { get; set; } = "en";
    public string Theme { get; set; } = "light";
    public int MaxConcurrency { get; set; } = 3;
    public ConversionEngine SelectedEngine { get; set; } = ConversionEngine.MarkItDown;
    public bool EnableOcr { get; set; } = false;
    public bool ForceFullPageOcr { get; set; } = false;
    public ImageExportMode ImageExportMode { get; set; } = ImageExportMode.None;
    
    // Engine selection (multiple selection support)
    public bool UseMarkItDown { get; set; } = true;
    public bool UseDocling { get; set; } = false;
    public bool UseDoclingGpu { get; set; } = false;
    public bool UsePaddleOcr { get; set; } = false;
    public bool UsePaddleOcrGpu { get; set; } = false;
}

public enum ConversionEngine
{
    MarkItDown,
    Docling,
    DoclingGpu,
    PaddleOcr
}

/// <summary>
/// Image export mode for Docling conversion
/// </summary>
public enum ImageExportMode
{
    /// <summary>No images - placeholder only</summary>
    None,
    /// <summary>Base64 embedded in markdown</summary>
    Embedded,
    /// <summary>External files in a subfolder</summary>
    ExternalFiles
}

/// <summary>
/// Conversion queue item - holds file conversion state
/// </summary>
public class QueueItem
{
    public string FileName { get; set; } = string.Empty;
    public string FilePath { get; set; } = string.Empty;
    public string FileType { get; set; } = string.Empty;
    public bool IsSelected { get; set; } = true;
    public ConversionStatus Status { get; set; } = ConversionStatus.Queued;
    public string? ErrorMessage { get; set; }
    public ConversionEngine? Engine { get; set; }
    public TimeSpan? ElapsedTime { get; set; }
    
    public string EngineName => Engine switch
    {
        ConversionEngine.MarkItDown => "MarkItDown",
        ConversionEngine.Docling => "Docling (CPU)",
        ConversionEngine.DoclingGpu => "Docling (GPU)",
        ConversionEngine.PaddleOcr => "PaddleOCR",
        _ => "Auto"
    };
    
    public string OutputSuffix => Engine switch
    {
        ConversionEngine.MarkItDown => "_it.md",
        ConversionEngine.Docling => "_dl.md",
        ConversionEngine.DoclingGpu => "_dlc.md",
        ConversionEngine.PaddleOcr => "_pd.md",
        _ => ".md"
    };
    
    public string ElapsedTimeText => ElapsedTime.HasValue 
        ? ElapsedTime.Value.TotalSeconds < 60 
            ? $"{ElapsedTime.Value.TotalSeconds:F1}s"
            : $"{(int)ElapsedTime.Value.TotalMinutes}m {ElapsedTime.Value.Seconds}s"
        : "";
}

public enum ConversionStatus
{
    Queued,
    Converting,
    Completed,
    Failed,
    Unsupported
}
