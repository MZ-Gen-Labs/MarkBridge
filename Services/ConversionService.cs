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
            string? doclingOutputPath = null;
            switch (engine)
            {
                case ConversionEngine.MarkItDown:
                    result = await RunMarkItDownAsync(pythonPath, inputPath, fullOutputPath, cancellationToken, onProgress);
                    break;
                case ConversionEngine.Docling:
                case ConversionEngine.DoclingGpu:
                    var doclingResult = await RunDoclingAsync(pythonPath, inputPath, fullOutputPath, options, 
                        engine == ConversionEngine.DoclingGpu, cancellationToken, onProgress);
                    result = doclingResult.output;
                    doclingOutputPath = doclingResult.outputFilePath;
                    break;
                default:
                    return new ConversionResult
                    {
                        Success = false,
                        ErrorMessage = $"Unknown conversion engine: {engine}"
                    };
            }

            var elapsed = DateTime.Now - startTime;

            // For Docling, use the returned output path
            var actualOutputPath = fullOutputPath;
            if (engine == ConversionEngine.Docling || engine == ConversionEngine.DoclingGpu)
            {
                // Docling handles file moving internally
                if (!string.IsNullOrEmpty(doclingOutputPath))
                {
                    actualOutputPath = doclingOutputPath;
                }
            }

            if (File.Exists(actualOutputPath))
            {
                return new ConversionResult
                {
                    Success = true,
                    OutputPath = actualOutputPath,
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

    private async Task<(string output, string? outputFilePath)> RunDoclingAsync(
        string pythonPath,
        string inputPath,
        string finalOutputPath,
        ConversionOptions options,
        bool useGpu,
        CancellationToken cancellationToken,
        Action<string>? onProgress)
    {
        // Get docling executable path from venv
        var venvDir = Path.GetDirectoryName(Path.GetDirectoryName(pythonPath));
        var doclingPath = Path.Combine(venvDir!, "Scripts", "docling.exe");
        
        if (!File.Exists(doclingPath))
        {
            return ("Docling CLI not found. Please install Docling first.", null);
        }

        // Create unique temp output directory to avoid conflicts in parallel processing
        var tempOutputDir = Path.Combine(Path.GetTempPath(), $"docling_{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempOutputDir);

        try
        {
            // Build docling command arguments
            var sb = new StringBuilder();
            sb.Append($"\"{inputPath}\" --to md --output \"{tempOutputDir}\"");

            if (options.EnableOcr)
            {
                sb.Append(" --ocr-engine tesseract");
            }

            // Image export mode: none (placeholder), embedded (base64), or external files (referenced)
            var imageMode = options.ImageExportMode switch
            {
                ImageExportMode.Embedded => "embedded",
                ImageExportMode.ExternalFiles => "referenced",
                _ => "placeholder"  // None or default
            };
            sb.Append($" --image-export-mode {imageMode}");

            // Explicitly set device to prevent Docling from auto-detecting GPU
            if (useGpu)
            {
                sb.Append(" --device cuda");
            }
            else
            {
                sb.Append(" --device cpu");
            }

            onProgress?.Invoke($"Running Docling{(useGpu ? " (GPU)" : "")}: {Path.GetFileName(inputPath)}");

            var result = await RunProcessAsync(doclingPath, sb.ToString(), cancellationToken, onProgress);

            // Find the output file in temp directory
            var expectedTempOutput = Path.Combine(tempOutputDir, 
                Path.GetFileNameWithoutExtension(inputPath) + ".md");
            
            if (File.Exists(expectedTempOutput))
            {
                // Move to final destination
                var finalDir = Path.GetDirectoryName(finalOutputPath);
                if (!string.IsNullOrEmpty(finalDir))
                {
                    Directory.CreateDirectory(finalDir);
                }
                
                // Delete existing file if present
                if (File.Exists(finalOutputPath))
                {
                    File.Delete(finalOutputPath);
                }
                
                File.Move(expectedTempOutput, finalOutputPath);
                return (result, finalOutputPath);
            }
            
            return (result, null);
        }
        finally
        {
            // Cleanup temp directory
            try
            {
                if (Directory.Exists(tempOutputDir))
                {
                    Directory.Delete(tempOutputDir, true);
                }
            }
            catch { }
        }
    }

    private async Task<string> RunProcessAsync(
        string exePath,
        string arguments,
        CancellationToken cancellationToken,
        Action<string>? onProgress)
    {
        var psi = new ProcessStartInfo
        {
            FileName = exePath,
            Arguments = arguments,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8
        };

        psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";

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

        using var timeoutCts = new CancellationTokenSource(TimeSpan.FromMinutes(30));
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
            CreateNoWindow = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8
        };

        // Force unbuffered output to prevent deadlock
        psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";
        psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";

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
    public ImageExportMode ImageExportMode { get; set; } = ImageExportMode.None;
    public int MaxRetries { get; set; } = 5;
}

