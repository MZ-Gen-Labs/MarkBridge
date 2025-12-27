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

    [Obsolete("Use MarkItDownVenvPath, DoclingVenvPath, or PaddleVenvPath instead")]
    public string VirtualEnvPath
    {
        get => _settings.VirtualEnvPath;
        set { _settings.VirtualEnvPath = value; NotifyStateChanged(); }
    }

    /// <summary>
    /// Base path for all virtual environments.
    /// Individual engine venvs are created as subdirectories (.venv_markitdown, .venv_docling, .venv_paddle)
    /// </summary>
    public string VenvBasePath
    {
        get => _settings.VenvBasePath;
        set 
        { 
            _settings.VenvBasePath = value;
            // Update individual venv paths based on new base path
            UpdateVenvPaths();
            NotifyStateChanged(); 
        }
    }

    /// <summary>
    /// Virtual environment path for MarkItDown engine (read-only, derived from VenvBasePath)
    /// </summary>
    public string MarkItDownVenvPath => string.IsNullOrEmpty(_settings.VenvBasePath) 
        ? string.Empty 
        : Path.Combine(_settings.VenvBasePath, ".venv_markitdown");

    /// <summary>
    /// Virtual environment path for Docling engine (read-only, derived from VenvBasePath)
    /// </summary>
    public string DoclingVenvPath => string.IsNullOrEmpty(_settings.VenvBasePath) 
        ? string.Empty 
        : Path.Combine(_settings.VenvBasePath, ".venv_docling");

    /// <summary>
    /// Virtual environment path for PaddleOCR engine (read-only, derived from VenvBasePath)
    /// </summary>
    public string PaddleVenvPath => string.IsNullOrEmpty(_settings.VenvBasePath) 
        ? string.Empty 
        : Path.Combine(_settings.VenvBasePath, ".venv_paddle");

    /// <summary>
    /// Update individual venv paths when base path changes (for internal use)
    /// </summary>
    private void UpdateVenvPaths()
    {
        // Paths are now computed properties, no need to update
        // This method is kept for any future side effects
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

    public bool UsePaddleOcrCpu
    {
        get => _settings.UsePaddleOcrCpu;
        set { _settings.UsePaddleOcrCpu = value; NotifyStateChanged(); }
    }

    public bool UsePaddleOcrGpu
    {
        get => _settings.UsePaddleOcrGpu;
        set { _settings.UsePaddleOcrGpu = value; NotifyStateChanged(); }
    }

    /// <summary>
    /// Use EasyOCR for Docling OCR
    /// </summary>
    public bool UseEasyOcr
    {
        get => _settings.UseEasyOcr;
        set { _settings.UseEasyOcr = value; NotifyStateChanged(); }
    }

    /// <summary>
    /// Use RapidOCR for Docling OCR
    /// </summary>
    public bool UseRapidOcr
    {
        get => _settings.UseRapidOcr;
        set { _settings.UseRapidOcr = value; NotifyStateChanged(); }
    }

    /// <summary>
    /// Use RapidOCR v5 (PP-OCRv5) for high-accuracy Japanese OCR
    /// </summary>
    public bool UseRapidOcrV5
    {
        get => _settings.UseRapidOcrV5;
        set { _settings.UseRapidOcrV5 = value; NotifyStateChanged(); }
    }

    /// <summary>
    /// Output file overwrite mode
    /// </summary>
    public OutputOverwriteMode OutputOverwriteMode
    {
        get => _settings.OutputOverwriteMode;
        set { _settings.OutputOverwriteMode = value; NotifyStateChanged(); }
    }

    #endregion

    #region Status

    public string StatusMessage { get; private set; } = "Ready";
    public bool IsProcessing { get; private set; }
    [Obsolete("Use IsMarkItDownVenvActive, IsDoclingVenvActive, or IsPaddleVenvActive instead")]
    public bool IsVenvActive { get; set; }
    public bool IsMarkItDownVenvActive { get; set; }
    public bool IsDoclingVenvActive { get; set; }
    public bool IsPaddleVenvActive { get; set; }
    public string? PythonVersion { get; set; }
    public string? MarkItDownVersion { get; set; }
    public string? DoclingVersion { get; set; }

    /// <summary>
    /// Returns true if legacy VirtualEnvPath is set and exists (old .venv folder)
    /// </summary>
    public bool HasLegacyVenv => !string.IsNullOrEmpty(_settings.VirtualEnvPath)
        && Directory.Exists(_settings.VirtualEnvPath)
        && !_settings.VirtualEnvPath.StartsWith(_settings.VenvBasePath);

    /// <summary>
    /// Path to the legacy VirtualEnv (if exists)
    /// </summary>
    public string LegacyVenvPath => _settings.VirtualEnvPath;

    /// <summary>
    /// Clear the legacy VirtualEnvPath from settings
    /// </summary>
    public void ClearLegacyVenv()
    {
        _settings.VirtualEnvPath = string.Empty;
        NotifyStateChanged();
    }

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

        // Set default VenvBasePath if not configured
        if (string.IsNullOrEmpty(_settings.VenvBasePath))
        {
            var appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            _settings.VenvBasePath = Path.Combine(appData, "MarkBridge");
        }

        // Legacy migration: if old VirtualEnvPath exists, clear it (venvs are now under VenvBasePath)
        if (!string.IsNullOrEmpty(_settings.VirtualEnvPath))
        {
            // Keep legacy path info for HasLegacyVenv check, but don't use it for new venvs
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
    public string VirtualEnvPath { get; set; } = string.Empty; // Legacy, kept for migration
    public string VenvBasePath { get; set; } = string.Empty; // New: parent folder for all venvs
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
    public bool UsePaddleOcrCpu { get; set; } = false;
    public bool UsePaddleOcrGpu { get; set; } = false;
    
    // Docling OCR engine selection (multiple selection support)
    public bool UseEasyOcr { get; set; } = true;
    public bool UseRapidOcr { get; set; } = false;
    public bool UseRapidOcrV5 { get; set; } = false;  // PP-OCRv5 Japanese optimized
    
    // Output file handling
    public OutputOverwriteMode OutputOverwriteMode { get; set; } = OutputOverwriteMode.Overwrite;
}

/// <summary>
/// Output file overwrite mode
/// </summary>
public enum OutputOverwriteMode
{
    /// <summary>Overwrite existing file</summary>
    Overwrite,
    /// <summary>Skip if file exists</summary>
    Skip,
    /// <summary>Save with new name (e.g., _1, _2)</summary>
    Rename
}

public enum ConversionEngine
{
    MarkItDown,
    Docling,
    DoclingGpu,
    PaddleOcrCpu,
    PaddleOcrGpu
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
    public string? OcrEngine { get; set; }  // "easyocr" or "rapidocr" for Docling
    public TimeSpan? ElapsedTime { get; set; }
    public DateTime? StartTime { get; set; }
    
    public string EngineName 
    {
        get
        {
            var baseName = Engine switch
            {
                ConversionEngine.MarkItDown => "MarkItDown",
                ConversionEngine.Docling => "Docling (CPU)",
                ConversionEngine.DoclingGpu => "Docling (GPU)",
                ConversionEngine.PaddleOcrCpu => "PaddleOCR (CPU)",
                ConversionEngine.PaddleOcrGpu => "PaddleOCR (GPU)",
                _ => "Auto"
            };
            
            // Append OCR engine info for Docling
            if ((Engine == ConversionEngine.Docling || Engine == ConversionEngine.DoclingGpu) && !string.IsNullOrEmpty(OcrEngine))
            {
                var ocrName = OcrEngine switch
                {
                    "easyocr" => "EasyOCR",
                    "rapidocr_v5" => "RapidOCR v5",
                    _ => "RapidOCR"
                };
                return $"{baseName} - {ocrName}";
            }
            
            return baseName;
        }
    }
    
    public string OutputSuffix
    {
        get
        {
            // Naming convention: _[engine][c/g for CPU/GPU][e/r for EasyOCR/RapidOCR]
            // Examples:
            //   MarkItDown     -> _it.md
            //   Docling CPU    -> _dlc.md (base) or _dlce.md / _dlcr.md (with OCR)
            //   Docling GPU    -> _dlg.md (base) or _dlge.md / _dlgr.md (with OCR)
            //   PaddleOCR CPU  -> _pdc.md
            //   PaddleOCR GPU  -> _pdg.md
            
            var baseSuffix = Engine switch
            {
                ConversionEngine.MarkItDown => "_it",
                ConversionEngine.Docling => "_dlc",      // Docling CPU
                ConversionEngine.DoclingGpu => "_dlg",   // Docling GPU
                ConversionEngine.PaddleOcrCpu => "_pdc", // PaddleOCR CPU
                ConversionEngine.PaddleOcrGpu => "_pdg", // PaddleOCR GPU
                _ => ""
            };
            
            // Append OCR engine suffix for Docling (e = EasyOCR, r = RapidOCR, v = RapidOCR v5)
            if ((Engine == ConversionEngine.Docling || Engine == ConversionEngine.DoclingGpu) && !string.IsNullOrEmpty(OcrEngine))
            {
                var ocrSuffix = OcrEngine switch
                {
                    "easyocr" => "e",
                    "rapidocr_v5" => "v",
                    _ => "r"
                };
                return $"{baseSuffix}{ocrSuffix}.md";
            }
            
            return $"{baseSuffix}.md";
        }
    }
    
    /// <summary>
    /// Gets elapsed time text - shows live elapsed for Converting status, final for Completed
    /// </summary>
    public string ElapsedTimeText 
    {
        get
        {
            var elapsed = Status == ConversionStatus.Converting && StartTime.HasValue
                ? DateTime.Now - StartTime.Value
                : ElapsedTime;
            
            if (!elapsed.HasValue) return "";
            
            return elapsed.Value.TotalSeconds < 60 
                ? $"{elapsed.Value.TotalSeconds:F1}s"
                : $"{(int)elapsed.Value.TotalMinutes}m {elapsed.Value.Seconds}s";
        }
    }
}

public enum ConversionStatus
{
    Queued,
    Converting,
    Completed,
    Failed,
    Unsupported
}
