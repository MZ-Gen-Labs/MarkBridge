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

    public bool IncludeImages
    {
        get => _settings.IncludeImages;
        set { _settings.IncludeImages = value; NotifyStateChanged(); }
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
    public int MaxConcurrency { get; set; } = 3;
    public ConversionEngine SelectedEngine { get; set; } = ConversionEngine.MarkItDown;
    public bool EnableOcr { get; set; } = false;
    public bool IncludeImages { get; set; } = false;
}

public enum ConversionEngine
{
    MarkItDown,
    Docling,
    DoclingGpu
}
