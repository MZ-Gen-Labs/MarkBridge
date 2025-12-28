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

            // Determine output filename based on engine and options
            var outputFileName = GetOutputFileName(Path.GetFileName(inputPath), engine, options);
            var fullOutputPath = Path.Combine(outputPath, outputFileName);

            // Ensure output directory exists
            Directory.CreateDirectory(outputPath);

            // Select venv based on engine type
            var venvPath = engine switch
            {
                ConversionEngine.MarkItDown => _appState.MarkItDownVenvPath,
                ConversionEngine.Docling or ConversionEngine.DoclingGpu => _appState.DoclingVenvPath,
                ConversionEngine.PaddleOcrCpu or ConversionEngine.PaddleOcrGpu => _appState.PaddleVenvPath,
                ConversionEngine.MarkerCpu or ConversionEngine.MarkerGpu => _appState.MarkerVenvPath,
                _ => _appState.MarkItDownVenvPath
            };
            var pythonPath = _pythonEnv.GetVenvPythonPath(venvPath);

            if (!File.Exists(pythonPath))
            {
                return new ConversionResult
                {
                    Success = false,
                    ErrorMessage = $"Python virtual environment not configured for {engine}. Path: {venvPath}"
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
                    // If RapidOCR v5 is selected, use Docling pipeline with PP-OCRv5 models for OCR
                    if (options.UseRapidOcrV5 && options.EnableOcr)
                    {
                        // Use Docling with RapidOCR configured to use PP-OCRv5 models
                        // This maintains table structure recognition while using high-accuracy PP-OCRv5 for OCR
                        result = await RunRapidOcrV5Async(pythonPath, inputPath, fullOutputPath, options, 
                            engine == ConversionEngine.DoclingGpu, cancellationToken, onProgress);
                        doclingOutputPath = File.Exists(fullOutputPath) ? fullOutputPath : null;
                    }
                    else
                    {
                        var doclingResult = await RunDoclingAsync(pythonPath, inputPath, fullOutputPath, options, 
                            engine == ConversionEngine.DoclingGpu, cancellationToken, onProgress);
                        result = doclingResult.output;
                        doclingOutputPath = doclingResult.outputFilePath;
                    }
                    break;
                case ConversionEngine.PaddleOcrCpu:
                    result = await RunPaddleOcrAsync(pythonPath, inputPath, fullOutputPath, false, cancellationToken, onProgress);
                    break;
                case ConversionEngine.PaddleOcrGpu:
                    result = await RunPaddleOcrAsync(pythonPath, inputPath, fullOutputPath, true, cancellationToken, onProgress);
                    break;
                case ConversionEngine.MarkerCpu:
                    result = await RunMarkerAsync(pythonPath, inputPath, fullOutputPath, false, options, cancellationToken, onProgress);
                    break;
                case ConversionEngine.MarkerGpu:
                    result = await RunMarkerAsync(pythonPath, inputPath, fullOutputPath, true, options, cancellationToken, onProgress);
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

    private string GetOutputFileName(string inputFileName, ConversionEngine engine, ConversionOptions? options)
    {
        var baseName = Path.GetFileNameWithoutExtension(inputFileName);
        
        // Naming convention: _[engine][c/g for CPU/GPU][e/r for EasyOCR/RapidOCR]
        var suffix = engine switch
        {
            ConversionEngine.MarkItDown => "_it",
            ConversionEngine.Docling => "_dlc",      // Docling CPU
            ConversionEngine.DoclingGpu => "_dlg",   // Docling GPU
            ConversionEngine.PaddleOcrCpu => "_pdc", // PaddleOCR CPU
            ConversionEngine.PaddleOcrGpu => "_pdg", // PaddleOCR GPU
            ConversionEngine.MarkerCpu => "_mkc",    // Marker CPU
            ConversionEngine.MarkerGpu => "_mkg",    // Marker GPU
            _ => ""
        };
        
        // Append OCR engine suffix for Docling (e = EasyOCR, r = RapidOCR, v = RapidOCR v5)
        if (engine == ConversionEngine.Docling || engine == ConversionEngine.DoclingGpu)
        {
            if (options?.UseEasyOcr == true && options?.UseRapidOcr != true && options?.UseRapidOcrV5 != true)
            {
                suffix += "e";
            }
            else if (options?.UseRapidOcrV5 == true && options?.UseEasyOcr != true && options?.UseRapidOcr != true)
            {
                suffix += "v";
            }
            else if (options?.UseRapidOcr == true && options?.UseEasyOcr != true && options?.UseRapidOcrV5 != true)
            {
                suffix += "r";
            }
            // If multiple or none, don't add OCR suffix
        }
        
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

    private async Task<string> RunPaddleOcrAsync(
        string pythonPath,
        string inputPath,
        string outputPath,
        bool useGpu,
        CancellationToken cancellationToken,
        Action<string>? onProgress)
    {
        var scriptPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Resources", "Python", "paddle_convert.py");
        // Fallback for development time if BaseDirectory is bin output
        if (!File.Exists(scriptPath))
        {
             // Try to find it in source tree if not copied to output yet
             var projectDir = Path.GetDirectoryName(Path.GetDirectoryName(Path.GetDirectoryName(AppDomain.CurrentDomain.BaseDirectory)));
             if (projectDir != null)
                 scriptPath = Path.Combine(projectDir, "Resources", "Python", "paddle_convert.py");
        }

        if (!File.Exists(scriptPath))
        {
            return "Error: paddle_convert.py script not found.";
        }

        var args = $"\"{scriptPath}\" \"{inputPath}\" \"{outputPath}\" --lang japan";
        if (useGpu)
        {
            args += " --use_gpu";
        }

        onProgress?.Invoke($"Running PaddleOCR{(useGpu ? " (GPU)" : "")}: {Path.GetFileName(inputPath)}");

        return await RunPythonProcessAsync(pythonPath, args, cancellationToken, onProgress);
    }

    private async Task<string> RunMarkerAsync(
        string pythonPath,
        string inputPath,
        string outputPath,
        bool useGpu,
        ConversionOptions? options,
        CancellationToken cancellationToken,
        Action<string>? onProgress)
    {
        // Get marker_single executable path from venv
        var venvDir = Path.GetDirectoryName(Path.GetDirectoryName(pythonPath));
        var markerPath = Path.Combine(venvDir!, "Scripts", "marker_single.exe");
        
        if (!File.Exists(markerPath))
        {
            return "Error: marker_single.exe not found. Please install Marker first.";
        }

        // Create output directory (Marker requires directory)
        var outputDir = Path.GetDirectoryName(outputPath);
        if (!Directory.Exists(outputDir))
        {
            Directory.CreateDirectory(outputDir!);
        }

        // Build command arguments
        var args = $"\"{inputPath}\" --output_dir \"{outputDir}\" --output_format markdown";
        
        // Add Marker-specific options
        if (options?.MarkerDisableOcr == true)
        {
            args += " --disable_ocr";
        }
        if (options?.MarkerDisableImageExtraction == true)
        {
            args += " --disable_image_extraction";
        }
        
        onProgress?.Invoke($"Running Marker{(useGpu ? " (GPU)" : " (CPU)")}: {Path.GetFileName(inputPath)}");

        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = markerPath,
                Arguments = args,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";
            
            // Set device based on GPU flag
            if (!useGpu)
            {
                psi.EnvironmentVariables["CUDA_VISIBLE_DEVICES"] = "";
            }

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

            await process.WaitForExitAsync(cancellationToken);

            // Marker creates output in a subdirectory named after the input file
            var inputName = Path.GetFileNameWithoutExtension(inputPath);
            var markerOutputDir = Path.Combine(outputDir!, inputName);
            var markerOutputFile = Path.Combine(markerOutputDir, $"{inputName}.md");
            
            // If output file exists in subdirectory, move it to expected location
            if (File.Exists(markerOutputFile))
            {
                // Move the markdown file to the expected output path
                File.Copy(markerOutputFile, outputPath, true);
                
                // Try to preserve images if any
                var imageFiles = Directory.GetFiles(markerOutputDir, "*.jpeg")
                    .Concat(Directory.GetFiles(markerOutputDir, "*.png"));
                    
                var imagesDir = Path.Combine(outputDir!, $"{Path.GetFileNameWithoutExtension(outputPath)}_images");
                if (imageFiles.Any())
                {
                    Directory.CreateDirectory(imagesDir);
                    foreach (var imageFile in imageFiles)
                    {
                        var destPath = Path.Combine(imagesDir, Path.GetFileName(imageFile));
                        File.Copy(imageFile, destPath, true);
                    }
                    
                    // Update image links in markdown
                    var mdContent = await File.ReadAllTextAsync(outputPath);
                    var updatedContent = mdContent.Replace($"({inputName}/", $"({Path.GetFileNameWithoutExtension(outputPath)}_images/");
                    await File.WriteAllTextAsync(outputPath, updatedContent);
                }
                
                // Clean up Marker's temp directory
                try { Directory.Delete(markerOutputDir, true); } catch { }
            }

            return process.ExitCode == 0 ? output.ToString() : error.ToString();
        }
        catch (Exception ex)
        {
            return $"Error: {ex.Message}";
        }
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

        // Create unique temp directory to avoid conflicts in parallel processing
        var tempDir = Path.Combine(Path.GetTempPath(), $"docling_{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        
        // Separate input and output temp directories
        var tempInputDir = Path.Combine(tempDir, "input");
        var tempOutputDir = Path.Combine(tempDir, "output");
        Directory.CreateDirectory(tempInputDir);
        Directory.CreateDirectory(tempOutputDir);

        try
        {
            // Copy input file to temp directory to avoid file access conflicts
            // when multiple engines process the same file simultaneously
            var inputFileName = Path.GetFileName(inputPath);
            var tempInputPath = Path.Combine(tempInputDir, inputFileName);
            File.Copy(inputPath, tempInputPath);
            
            // Build docling command arguments
            var sb = new StringBuilder();
            sb.Append($"\"{tempInputPath}\" --to md --output \"{tempOutputDir}\"");

            if (options.EnableOcr)
            {
                // Determine OCR engine - if both selected, use EasyOCR (caller should create separate queue items)
                var ocrEngine = options.UseEasyOcr ? "easyocr" : (options.UseRapidOcr ? "rapidocr" : "easyocr");
                sb.Append($" --ocr-engine {ocrEngine} --ocr-lang ja,en");
                
                // Force OCR for all pages (useful for scanned documents)
                if (options.ForceFullPageOcr)
                {
                    sb.Append(" --force-ocr");
                }
            }
            else
            {
                // Explicitly disable OCR
                sb.Append(" --no-ocr");
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
                
                // Copy image files if using referenced mode
                if (options.ImageExportMode == ImageExportMode.ExternalFiles)
                {
                    // Docling creates images in the output directory with various naming patterns
                    // Copy all image files to final destination
                    var imageExtensions = new[] { ".png", ".jpg", ".jpeg", ".gif", ".webp" };
                    foreach (var imgFile in Directory.GetFiles(tempOutputDir))
                    {
                        var ext = Path.GetExtension(imgFile).ToLower();
                        if (imageExtensions.Contains(ext))
                        {
                            var destPath = Path.Combine(finalDir!, Path.GetFileName(imgFile));
                            if (File.Exists(destPath))
                            {
                                File.Delete(destPath);
                            }
                            File.Copy(imgFile, destPath);
                        }
                    }
                    
                    // Also check for images subdirectory
                    var imagesDir = Path.Combine(tempOutputDir, "images");
                    if (Directory.Exists(imagesDir))
                    {
                        var destImagesDir = Path.Combine(finalDir!, "images");
                        Directory.CreateDirectory(destImagesDir);
                        foreach (var imgFile in Directory.GetFiles(imagesDir))
                        {
                            var destPath = Path.Combine(destImagesDir, Path.GetFileName(imgFile));
                            if (File.Exists(destPath))
                            {
                                File.Delete(destPath);
                            }
                            File.Copy(imgFile, destPath);
                        }
                    }
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
                if (Directory.Exists(tempDir))
                {
                    Directory.Delete(tempDir, true);
                }
            }
            catch { }
        }
    }

    private async Task<string> RunRapidOcrV5Async(
        string pythonPath,
        string inputPath,
        string outputPath,
        ConversionOptions options,
        bool useGpu,
        CancellationToken cancellationToken,
        Action<string>? onProgress)
    {
        // Use docling_v5_convert.py which uses Docling's pipeline with RapidOCR configured to use PP-OCRv5 models
        // This maintains table structure recognition while using high-accuracy PP-OCRv5 for OCR
        var scriptPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Resources", "Python", "docling_v5_convert.py");
        // Fallback for development time if BaseDirectory is bin output
        if (!File.Exists(scriptPath))
        {
             // Try to find it in source tree if not copied to output yet
             var projectDir = Path.GetDirectoryName(Path.GetDirectoryName(Path.GetDirectoryName(AppDomain.CurrentDomain.BaseDirectory)));
             if (projectDir != null)
                 scriptPath = Path.Combine(projectDir, "Resources", "Python", "docling_v5_convert.py");
        }

        if (!File.Exists(scriptPath))
        {
            return "Error: docling_v5_convert.py script not found.";
        }

        // Build arguments
        var args = new StringBuilder();
        args.Append($"\"{scriptPath}\" \"{inputPath}\" \"{outputPath}\"");
        
        if (useGpu)
        {
            args.Append(" --gpu");
        }
        
        if (options.ForceFullPageOcr)
        {
            args.Append(" --force-ocr");
        }
        
        if (!options.EnableOcr)
        {
            args.Append(" --no-ocr");
        }
        
        var imageMode = options.ImageExportMode switch
        {
            ImageExportMode.Embedded => "embedded",
            ImageExportMode.ExternalFiles => "referenced",
            _ => "placeholder"
        };
        args.Append($" --image-mode {imageMode}");

        onProgress?.Invoke($"Running Docling with PP-OCRv5{(useGpu ? " (GPU)" : "")}: {Path.GetFileName(inputPath)}");

        return await RunPythonProcessAsync(pythonPath, args.ToString(), cancellationToken, onProgress);
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
    public bool ForceFullPageOcr { get; set; }
    public ImageExportMode ImageExportMode { get; set; } = ImageExportMode.None;
    public int MaxRetries { get; set; } = 5;
    
    /// <summary>
    /// Use EasyOCR for Docling OCR
    /// </summary>
    public bool UseEasyOcr { get; set; }
    
    /// <summary>
    /// Use RapidOCR for Docling OCR
    /// </summary>
    public bool UseRapidOcr { get; set; }
    
    /// <summary>
    /// Use RapidOCR v5 (PP-OCRv5) for high-accuracy Japanese OCR
    /// </summary>
    public bool UseRapidOcrV5 { get; set; }
    
    /// <summary>
    /// Output file overwrite mode
    /// </summary>
    public OutputOverwriteMode OutputOverwriteMode { get; set; } = OutputOverwriteMode.Overwrite;
    
    // Marker-specific options
    public bool MarkerDisableOcr { get; set; }
    public bool MarkerDisableImageExtraction { get; set; }
}

