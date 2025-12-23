using System.Diagnostics;
using System.Text;

namespace MarkBridge.Services;

/// <summary>
/// Service for file conversion using MarkItDown and Docling
/// </summary>
public class ConversionService
{
    private readonly AppStateService _appState;
    private readonly PythonEnvironmentService _pythonEnv;

    public ConversionService(AppStateService appState, PythonEnvironmentService pythonEnv)
    {
        _appState = appState;
        _pythonEnv = pythonEnv;
    }

    /// <summary>
    /// Convert a file using the specified engine
    /// </summary>
    public async Task<ConversionResult> ConvertFileAsync(
        string inputPath,
        string outputPath,
        ConversionEngine engine,
        ConversionOptions options,
        CancellationToken cancellationToken = default,
        Action<string>? onProgress = null)
    {
        var startTime = DateTime.Now;

        try
        {
            if (!File.Exists(inputPath))
            {
                return new ConversionResult
                {
                    Success = false,
                    ErrorMessage = $"Input file not found: {inputPath}"
                };
            }

            // Determine output filename based on engine
            var outputFileName = GetOutputFileName(Path.GetFileName(inputPath), engine);
            var fullOutputPath = Path.Combine(outputPath, outputFileName);

            // Ensure output directory exists
            Directory.CreateDirectory(outputPath);

            var venvPath = _appState.VirtualEnvPath;
            var pythonPath = _pythonEnv.GetVenvPythonPath(venvPath);

            if (!File.Exists(pythonPath))
            {
                return new ConversionResult
                {
                    Success = false,
                    ErrorMessage = "Python virtual environment not configured"
                };
            }

            string result;
            switch (engine)
            {
                case ConversionEngine.MarkItDown:
                    result = await RunMarkItDownAsync(pythonPath, inputPath, fullOutputPath, cancellationToken, onProgress);
                    break;
                case ConversionEngine.Docling:
                case ConversionEngine.DoclingGpu:
                    result = await RunDoclingAsync(pythonPath, inputPath, fullOutputPath, options, 
                        engine == ConversionEngine.DoclingGpu, cancellationToken, onProgress);
                    break;
                default:
                    return new ConversionResult
                    {
                        Success = false,
                        ErrorMessage = $"Unknown conversion engine: {engine}"
                    };
            }

            var elapsed = DateTime.Now - startTime;

            if (File.Exists(fullOutputPath))
            {
                return new ConversionResult
                {
                    Success = true,
                    OutputPath = fullOutputPath,
                    ElapsedTime = elapsed
                };
            }
            else
            {
                return new ConversionResult
                {
                    Success = false,
                    ErrorMessage = $"Output file was not created. Process output: {result}",
                    ElapsedTime = elapsed
                };
            }
        }
        catch (OperationCanceledException)
        {
            return new ConversionResult
            {
                Success = false,
                ErrorMessage = "Conversion was cancelled"
            };
        }
        catch (Exception ex)
        {
            return new ConversionResult
            {
                Success = false,
                ErrorMessage = $"Conversion error: {ex.Message}"
            };
        }
    }

    private string GetOutputFileName(string inputFileName, ConversionEngine engine)
    {
        var baseName = Path.GetFileNameWithoutExtension(inputFileName);
        var suffix = engine switch
        {
            ConversionEngine.MarkItDown => "_it",
            ConversionEngine.Docling => "_dl",
            ConversionEngine.DoclingGpu => "_dlc",
            _ => ""
        };
        return $"{baseName}{suffix}.md";
    }

    private async Task<string> RunMarkItDownAsync(
        string pythonPath,
        string inputPath,
        string outputPath,
        CancellationToken cancellationToken,
        Action<string>? onProgress)
    {
        // Using markitdown CLI: markitdown <input_file> -o <output_file>
        var args = $"-m markitdown \"{inputPath}\" -o \"{outputPath}\"";

        onProgress?.Invoke($"Running MarkItDown: {Path.GetFileName(inputPath)}");

        return await RunPythonProcessAsync(pythonPath, args, cancellationToken, onProgress);
    }

    private async Task<string> RunDoclingAsync(
        string pythonPath,
        string inputPath,
        string outputPath,
        ConversionOptions options,
        bool useGpu,
        CancellationToken cancellationToken,
        Action<string>? onProgress)
    {
        // Build docling command
        var sb = new StringBuilder();
        sb.Append($"-m docling \"{inputPath}\" --output \"{outputPath}\"");

        if (options.EnableOcr)
        {
            sb.Append(" --ocr");
        }

        if (options.IncludeImages)
        {
            sb.Append(" --export-images");
        }

        if (useGpu)
        {
            sb.Append(" --device cuda");
        }

        onProgress?.Invoke($"Running Docling{(useGpu ? " (GPU)" : "")}: {Path.GetFileName(inputPath)}");

        return await RunPythonProcessAsync(pythonPath, sb.ToString(), cancellationToken, onProgress);
    }

    private async Task<string> RunPythonProcessAsync(
        string pythonPath,
        string arguments,
        CancellationToken cancellationToken,
        Action<string>? onProgress)
    {
        var psi = new ProcessStartInfo
        {
            FileName = pythonPath,
            Arguments = arguments,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        // Force unbuffered output to prevent deadlock
        psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";

        using var process = new Process { StartInfo = psi };
        var output = new StringBuilder();
        var error = new StringBuilder();

        process.OutputDataReceived += (s, e) =>
        {
            if (e.Data != null)
            {
                output.AppendLine(e.Data);
                onProgress?.Invoke(e.Data);
            }
        };

        process.ErrorDataReceived += (s, e) =>
        {
            if (e.Data != null)
            {
                error.AppendLine(e.Data);
            }
        };

        process.Start();
        process.BeginOutputReadLine();
        process.BeginErrorReadLine();

        // Wait with timeout (10 minutes for large files / model downloads)
        using var timeoutCts = new CancellationTokenSource(TimeSpan.FromMinutes(10));
        using var linkedCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken, timeoutCts.Token);

        try
        {
            await process.WaitForExitAsync(linkedCts.Token);
        }
        catch (OperationCanceledException)
        {
            try
            {
                process.Kill(entireProcessTree: true);
            }
            catch { }
            throw;
        }

        if (error.Length > 0)
        {
            return $"Output:\n{output}\n\nErrors:\n{error}";
        }

        return output.ToString();
    }

    /// <summary>
    /// Get list of supported file extensions
    /// </summary>
    public static string[] SupportedExtensions => new[]
    {
        ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls",
        ".html", ".htm", ".xml", ".json", ".csv", ".epub", ".zip"
    };

    /// <summary>
    /// Check if a file extension is supported
    /// </summary>
    public static bool IsSupported(string filePath)
    {
        var ext = Path.GetExtension(filePath).ToLowerInvariant();
        return SupportedExtensions.Contains(ext);
    }
}

public class ConversionResult
{
    public bool Success { get; set; }
    public string? OutputPath { get; set; }
    public string? ErrorMessage { get; set; }
    public TimeSpan ElapsedTime { get; set; }
}

public class ConversionOptions
{
    public bool EnableOcr { get; set; }
    public bool IncludeImages { get; set; }
    public int MaxRetries { get; set; } = 5;
}
