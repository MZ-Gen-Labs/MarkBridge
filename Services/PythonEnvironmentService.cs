using System.Diagnostics;
using System.Text;
using System.Text.RegularExpressions;

namespace MarkBridge.Services;

/// <summary>
/// Service for managing Python environment and virtual environments
/// </summary>
public class PythonEnvironmentService
{
    private readonly AppStateService _appState;

    public PythonEnvironmentService(AppStateService appState)
    {
        _appState = appState;
    }

    #region Python Detection

    /// <summary>
    /// Auto-detect Python installation
    /// </summary>
    public async Task<(bool found, string path, string version)> AutoDetectPythonAsync()
    {
        // Common Python paths on Windows
        var candidatePaths = new List<string>
        {
            "python",
            "python3",
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python313", "python.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python312", "python.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python311", "python.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python310", "python.exe"),
            @"C:\Python313\python.exe",
            @"C:\Python312\python.exe",
            @"C:\Python311\python.exe",
            @"C:\Python310\python.exe",
        };

        foreach (var path in candidatePaths)
        {
            var result = await ValidatePythonAsync(path);
            if (result.isValid)
            {
                return (true, result.fullPath, result.version);
            }
        }

        return (false, string.Empty, string.Empty);
    }

    /// <summary>
    /// Validate a Python path and get version
    /// </summary>
    public async Task<(bool isValid, string fullPath, string version)> ValidatePythonAsync(string pythonPath)
    {
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = "--version",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            if (process == null) return (false, string.Empty, string.Empty);

            var output = await process.StandardOutput.ReadToEndAsync();
            var error = await process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();

            var versionText = !string.IsNullOrEmpty(output) ? output : error;
            var match = Regex.Match(versionText, @"Python (\d+\.\d+\.\d+)");

            if (match.Success)
            {
                var version = match.Groups[1].Value;
                var versionParts = version.Split('.');
                if (int.TryParse(versionParts[0], out int major) && 
                    int.TryParse(versionParts[1], out int minor))
                {
                    if (major >= 3 && minor >= 10)
                    {
                        // Get full path
                        var fullPath = pythonPath;
                        if (!Path.IsPathRooted(pythonPath))
                        {
                            var whereResult = await RunCommandAsync("where", pythonPath);
                            if (!string.IsNullOrEmpty(whereResult))
                            {
                                fullPath = whereResult.Split('\n')[0].Trim();
                            }
                        }
                        return (true, fullPath, version);
                    }
                }
            }
        }
        catch { }

        return (false, string.Empty, string.Empty);
    }

    #endregion

    #region Virtual Environment

    /// <summary>
    /// Check if virtual environment exists and is valid
    /// </summary>
    public bool IsVenvValid(string venvPath)
    {
        var pythonExe = GetVenvPythonPath(venvPath);
        return File.Exists(pythonExe);
    }

    /// <summary>
    /// Get the python.exe path inside venv
    /// </summary>
    public string GetVenvPythonPath(string venvPath)
    {
        return Path.Combine(venvPath, "Scripts", "python.exe");
    }

    /// <summary>
    /// Get the pip.exe path inside venv
    /// </summary>
    public string GetVenvPipPath(string venvPath)
    {
        return Path.Combine(venvPath, "Scripts", "pip.exe");
    }

    /// <summary>
    /// Create virtual environment
    /// </summary>
    public async Task<(bool success, string message)> CreateVenvAsync(string systemPythonPath, string venvPath, Action<string>? onProgress = null)
    {
        try
        {
            onProgress?.Invoke("Creating virtual environment...");

            // Delete existing if present
            if (Directory.Exists(venvPath))
            {
                Directory.Delete(venvPath, true);
            }

            var psi = new ProcessStartInfo
            {
                FileName = systemPythonPath,
                Arguments = $"-m venv \"{venvPath}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

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
                    onProgress?.Invoke(e.Data);
                }
            };

            process.Start();
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();

            await process.WaitForExitAsync();

            if (process.ExitCode == 0 && IsVenvValid(venvPath))
            {
                onProgress?.Invoke("Upgrading pip...");
                await UpgradePipAsync(venvPath, onProgress);
                return (true, "Virtual environment created successfully.");
            }

            return (false, $"Failed to create venv: {error}");
        }
        catch (Exception ex)
        {
            return (false, $"Error: {ex.Message}");
        }
    }

    /// <summary>
    /// Delete virtual environment
    /// </summary>
    public (bool success, string message) DeleteVenv(string venvPath)
    {
        try
        {
            if (Directory.Exists(venvPath))
            {
                Directory.Delete(venvPath, true);
                return (true, "Virtual environment deleted.");
            }
            return (true, "Virtual environment does not exist.");
        }
        catch (Exception ex)
        {
            return (false, $"Failed to delete: {ex.Message}");
        }
    }

    private async Task UpgradePipAsync(string venvPath, Action<string>? onProgress = null)
    {
        var pythonPath = GetVenvPythonPath(venvPath);
        await RunPipCommandAsync(pythonPath, "install --upgrade pip", onProgress);
    }

    #endregion

    #region Package Installation

    /// <summary>
    /// Check if MarkItDown is installed
    /// </summary>
    public async Task<(bool installed, string? version)> CheckMarkItDownAsync(string venvPath)
    {
        return await CheckPackageAsync(venvPath, "markitdown");
    }

    /// <summary>
    /// Check if Docling is installed
    /// </summary>
    public async Task<(bool installed, string? version)> CheckDoclingAsync(string venvPath)
    {
        return await CheckPackageAsync(venvPath, "docling");
    }

    /// <summary>
    /// Check if PyTorch with CUDA is installed and get CUDA version
    /// </summary>
    public async Task<(bool installed, string? torchVersion, string? cudaVersion)> CheckCudaAsync(string venvPath)
    {
        try
        {
            var pythonPath = GetVenvPythonPath(venvPath);
            var psi = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = "-c \"import torch; print(torch.__version__); print(torch.version.cuda if torch.cuda.is_available() else 'N/A')\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            if (process == null) return (false, null, null);

            var output = await process.StandardOutput.ReadToEndAsync();
            await process.WaitForExitAsync();

            if (process.ExitCode == 0 && !string.IsNullOrEmpty(output))
            {
                var lines = output.Trim().Split('\n');
                if (lines.Length >= 2)
                {
                    var torchVersion = lines[0].Trim();
                    var cudaVersion = lines[1].Trim();
                    if (cudaVersion != "N/A")
                    {
                        return (true, torchVersion, cudaVersion);
                    }
                }
            }
        }
        catch { }

        return (false, null, null);
    }

    /// <summary>
    /// Install MarkItDown
    /// </summary>
    public async Task<(bool success, string message)> InstallMarkItDownAsync(string venvPath, Action<string>? onProgress = null)
    {
        onProgress?.Invoke("Installing MarkItDown...");
        var result = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "install markitdown[all]", onProgress);
        return result.exitCode == 0
            ? (true, "MarkItDown installed successfully.")
            : (false, $"Installation failed: {result.error}");
    }

    /// <summary>
    /// Install Docling
    /// </summary>
    public async Task<(bool success, string message)> InstallDoclingAsync(string venvPath, Action<string>? onProgress = null)
    {
        onProgress?.Invoke("Installing Docling...");
        var result = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "install docling", onProgress);
        if (result.exitCode != 0)
        {
            return (false, $"Docling installation failed: {result.error}");
        }

        // Install onnxruntime for RapidOCR support
        onProgress?.Invoke("Installing onnxruntime for RapidOCR...");
        var onnxResult = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "install onnxruntime", onProgress);
        if (onnxResult.exitCode != 0)
        {
            return (false, $"onnxruntime installation failed: {onnxResult.error}");
        }

        return (true, "Docling installed successfully.");
    }

    /// <summary>
    /// Check if EasyOCR is installed (via docling[easyocr])
    /// </summary>
    public async Task<(bool installed, string? version)> CheckEasyOcrAsync(string venvPath)
    {
        return await CheckPackageAsync(venvPath, "easyocr");
    }

    /// <summary>
    /// Install EasyOCR for Docling
    /// </summary>
    public async Task<(bool success, string message)> InstallEasyOcrAsync(string venvPath, Action<string>? onProgress = null)
    {
        onProgress?.Invoke("Installing EasyOCR for Docling OCR...");
        var result = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "install \"docling[easyocr]\"", onProgress);
        return result.exitCode == 0
            ? (true, "EasyOCR installed successfully.")
            : (false, $"Installation failed: {result.error}");
    }

    /// <summary>
    /// Check if RapidOCR is installed (alternative OCR engine for Docling)
    /// </summary>
    public async Task<(bool installed, string? version)> CheckRapidOcrAsync(string venvPath)
    {
        // The package is installed as 'rapidocr' (not rapidocr-onnxruntime)
        return await CheckPackageAsync(venvPath, "rapidocr");
    }

    /// <summary>
    /// Install RapidOCR for Docling (alternative to EasyOCR - faster, lightweight)
    /// </summary>
    public async Task<(bool success, string message)> InstallRapidOcrAsync(string venvPath, Action<string>? onProgress = null)
    {
        onProgress?.Invoke("Installing RapidOCR for Docling...");
        var result = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "install \"docling[rapidocr]\"", onProgress);
        return result.exitCode == 0
            ? (true, "RapidOCR installed successfully.")
            : (false, $"Installation failed: {result.error}");
    }

    /// <summary>
    /// Check if RapidOCR v5 (PP-OCRv5 models) is installed
    /// </summary>
    public async Task<(bool installed, string? version)> CheckRapidOcrV5Async(string venvPath)
    {
        // Check if rapidocr_onnxruntime is installed
        var result = await CheckPackageAsync(venvPath, "rapidocr-onnxruntime");
        if (!result.installed)
        {
            return (false, null);
        }
        
        // Check if PP-OCRv5 models are downloaded
        var modelsDir = GetRapidOcrV5ModelsDir();
        var modelFiles = new[] { "PP-OCRv5_server_det_infer.onnx", "PP-OCRv5_server_rec_infer.onnx" };
        foreach (var file in modelFiles)
        {
            if (!File.Exists(Path.Combine(modelsDir, file)))
            {
                return (false, result.version);  // Package installed but models not downloaded
            }
        }
        
        return (true, result.version);
    }
    
    /// <summary>
    /// Get the directory for RapidOCR v5 models
    /// </summary>
    public string GetRapidOcrV5ModelsDir()
    {
        var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        return Path.Combine(localAppData, "MarkBridge", "models", "rapidocr_v5");
    }

    /// <summary>
    /// Install RapidOCR v5 with PP-OCRv5 models (high-accuracy Japanese OCR)
    /// </summary>
    public async Task<(bool success, string message)> InstallRapidOcrV5Async(string venvPath, Action<string>? onProgress = null)
    {
        var pythonPath = GetVenvPythonPath(venvPath);
        
        // 1. Install rapidocr_onnxruntime and dependencies
        onProgress?.Invoke("Installing rapidocr_onnxruntime...");
        var result = await RunPipCommandAsync(pythonPath, "install rapidocr_onnxruntime", onProgress);
        if (result.exitCode != 0)
        {
            return (false, $"Failed to install rapidocr_onnxruntime: {result.error}");
        }
        
        // 2. Install huggingface_hub for model download
        onProgress?.Invoke("Installing huggingface_hub...");
        var hfResult = await RunPipCommandAsync(pythonPath, "install huggingface_hub", onProgress);
        if (hfResult.exitCode != 0)
        {
            return (false, $"Failed to install huggingface_hub: {hfResult.error}");
        }
        
        // 3. Install numpy, opencv-python-headless, pymupdf for image processing
        onProgress?.Invoke("Installing image processing dependencies...");
        var imgResult = await RunPipCommandAsync(pythonPath, "install numpy opencv-python-headless pymupdf", onProgress);
        if (imgResult.exitCode != 0)
        {
            return (false, $"Failed to install image dependencies: {imgResult.error}");
        }
        
        // 4. Download PP-OCRv5 models using the Python script
        onProgress?.Invoke("Downloading PP-OCRv5 models from HuggingFace...");
        var scriptPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Resources", "Python", "rapidocr_v5_convert.py");
        // Fallback for development
        if (!File.Exists(scriptPath))
        {
            var projectDir = Path.GetDirectoryName(Path.GetDirectoryName(Path.GetDirectoryName(AppDomain.CurrentDomain.BaseDirectory)));
            if (projectDir != null)
                scriptPath = Path.Combine(projectDir, "Resources", "Python", "rapidocr_v5_convert.py");
        }
        
        if (!File.Exists(scriptPath))
        {
            return (false, "rapidocr_v5_convert.py script not found.");
        }
        
        var dlResult = await RunPythonScriptAsync(pythonPath, $"\"{scriptPath}\" --download-models", onProgress);
        if (dlResult.exitCode != 0)
        {
            return (false, $"Failed to download PP-OCRv5 models: {dlResult.error}");
        }
        
        return (true, "RapidOCR v5 with PP-OCRv5 models installed successfully.");
    }
    
    private async Task<(int exitCode, string output, string error)> RunPythonScriptAsync(
        string pythonPath, string args, Action<string>? onProgress = null)
    {
        var psi = new ProcessStartInfo
        {
            FileName = pythonPath,
            Arguments = args,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };
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

        await process.WaitForExitAsync();

        return (process.ExitCode, output.ToString(), error.ToString());
    }

    /// <summary>
    /// Check if PaddleOCR is installed
    /// </summary>
    public async Task<(bool installed, string? version)> CheckPaddleOcrAsync(string venvPath)
    {
        return await CheckPackageAsync(venvPath, "paddleocr");
    }

    /// <summary>
    /// Check if PaddlePaddle GPU is installed
    /// </summary>
    public async Task<(bool installed, string? version)> CheckPaddleGpuAsync(string venvPath)
    {
        return await CheckPackageAsync(venvPath, "paddlepaddle-gpu");
    }

    /// <summary>
    /// Check if PaddlePaddle CPU is installed
    /// </summary>
    public async Task<(bool installed, string? version)> CheckPaddleCpuAsync(string venvPath)
    {
        return await CheckPackageAsync(venvPath, "paddlepaddle");
    }

    /// <summary>
    /// Install PaddleOCR with CPU-only PaddlePaddle (no GPU required)
    /// </summary>
    public async Task<(bool success, string message)> InstallPaddleOcrCpuAsync(string venvPath, Action<string>? onProgress = null)
    {
        onProgress?.Invoke("Installing PaddlePaddle (CPU only)...");
        // 1. Install CPU-only PaddlePaddle
        var resultCpu = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "install paddlepaddle", onProgress);
        
        if (resultCpu.exitCode != 0)
        {
             return (false, $"PaddlePaddle installation failed: {resultCpu.error}");
        }

        onProgress?.Invoke("Installing PaddleOCR and dependencies...");
        // 2. Install generic packages from standard PyPI
        var resultLibs = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "install paddleocr opencv-python-headless \"paddlex[ocr]\" pymupdf", onProgress);

        return resultLibs.exitCode == 0
            ? (true, "PaddleOCR (CPU) installed successfully.")
            : (false, $"Dependency installation failed: {resultLibs.error}");
    }

    /// <summary>
    /// Install PaddleOCR with GPU-accelerated PaddlePaddle (CUDA 12.9)
    /// </summary>
    public async Task<(bool success, string message)> InstallPaddleOcrGpuAsync(string venvPath, Action<string>? onProgress = null)
    {
        onProgress?.Invoke("Installing PaddlePaddle GPU (CUDA 12.9)...");
        // 1. Install GPU engine specifically from the CUDA 12.9 index
        var resultGpu = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "install paddlepaddle-gpu -i https://www.paddlepaddle.org.cn/packages/stable/cu129/", onProgress);
        
        if (resultGpu.exitCode != 0)
        {
             return (false, $"PaddlePaddle-GPU installation failed: {resultGpu.error}");
        }

        onProgress?.Invoke("Installing PaddleOCR and dependencies...");
        // 2. Install generic packages from standard PyPI
        var resultLibs = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "install paddleocr opencv-python-headless \"paddlex[ocr]\" pymupdf", onProgress);

        return resultLibs.exitCode == 0
            ? (true, "PaddleOCR (GPU) installed successfully.")
            : (false, $"Dependency installation failed: {resultLibs.error}");
    }

    /// <summary>
    /// Install PyTorch with CUDA support
    /// </summary>
    public async Task<(bool success, string message)> InstallCudaSupportAsync(string venvPath, bool useNightly, Action<string>? onProgress = null)
    {
        var pythonPath = GetVenvPythonPath(venvPath);

        if (useNightly)
        {
            // RTX 50 series (Blackwell) requires CUDA 12.8 nightly
            onProgress?.Invoke("Installing PyTorch Nightly (CUDA 12.8) for RTX 50 series...");
            var torchResult = await RunPipCommandAsync(pythonPath,
                "install --force-reinstall --pre torch --index-url https://download.pytorch.org/whl/nightly/cu128", onProgress);

            if (torchResult.exitCode != 0)
                return (false, $"Failed to install PyTorch: {torchResult.error}");

            onProgress?.Invoke("Installing torchvision...");
            var visionResult = await RunPipCommandAsync(pythonPath,
                "install --force-reinstall --pre torchvision --no-deps --index-url https://download.pytorch.org/whl/nightly/cu128", onProgress);

            return visionResult.exitCode == 0
                ? (true, "CUDA support (Nightly/cu128) installed successfully.")
                : (false, $"Failed to install torchvision: {visionResult.error}");
        }
        else
        {
            // Standard CUDA 12.4
            onProgress?.Invoke("Installing PyTorch with CUDA 12.4...");
            var result = await RunPipCommandAsync(pythonPath,
                "install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu124", onProgress);

            return result.exitCode == 0
                ? (true, "CUDA support installed successfully.")
                : (false, $"Failed to install: {result.error}");
        }
    }

    #endregion

    #region Package Uninstall

    /// <summary>
    /// Uninstall MarkItDown
    /// </summary>
    public async Task<(bool success, string message)> UninstallMarkItDownAsync(string venvPath, Action<string>? onProgress = null)
    {
        onProgress?.Invoke("Uninstalling MarkItDown...");
        var result = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "uninstall markitdown -y", onProgress);
        return result.exitCode == 0
            ? (true, "MarkItDown uninstalled successfully.")
            : (false, $"Uninstall failed: {result.error}");
    }

    /// <summary>
    /// Uninstall Docling (Warning: This will disable OCR functionality)
    /// </summary>
    public async Task<(bool success, string message)> UninstallDoclingAsync(string venvPath, Action<string>? onProgress = null)
    {
        onProgress?.Invoke("Uninstalling Docling...");
        var result = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "uninstall docling -y", onProgress);
        return result.exitCode == 0
            ? (true, "Docling uninstalled successfully.")
            : (false, $"Uninstall failed: {result.error}");
    }

    /// <summary>
    /// Uninstall EasyOCR
    /// </summary>
    public async Task<(bool success, string message)> UninstallEasyOcrAsync(string venvPath, Action<string>? onProgress = null)
    {
        onProgress?.Invoke("Uninstalling EasyOCR...");
        var result = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "uninstall easyocr -y", onProgress);
        return result.exitCode == 0
            ? (true, "EasyOCR uninstalled successfully.")
            : (false, $"Uninstall failed: {result.error}");
    }

    /// <summary>
    /// Uninstall RapidOCR
    /// </summary>
    public async Task<(bool success, string message)> UninstallRapidOcrAsync(string venvPath, Action<string>? onProgress = null)
    {
        onProgress?.Invoke("Uninstalling RapidOCR...");
        var result = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "uninstall rapidocr -y", onProgress);
        return result.exitCode == 0
            ? (true, "RapidOCR uninstalled successfully.")
            : (false, $"Uninstall failed: {result.error}");
    }

    /// <summary>
    /// Uninstall PaddleOCR (CPU version)
    /// </summary>
    public async Task<(bool success, string message)> UninstallPaddleOcrCpuAsync(string venvPath, Action<string>? onProgress = null)
    {
        onProgress?.Invoke("Uninstalling PaddleOCR (CPU)...");
        var result = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "uninstall paddleocr paddlepaddle -y", onProgress);
        return result.exitCode == 0
            ? (true, "PaddleOCR (CPU) uninstalled successfully.")
            : (false, $"Uninstall failed: {result.error}");
    }

    /// <summary>
    /// Uninstall PaddleOCR (GPU version)
    /// </summary>
    public async Task<(bool success, string message)> UninstallPaddleOcrGpuAsync(string venvPath, Action<string>? onProgress = null)
    {
        onProgress?.Invoke("Uninstalling PaddleOCR (GPU)...");
        var result = await RunPipCommandAsync(GetVenvPythonPath(venvPath), "uninstall paddleocr paddlepaddle-gpu -y", onProgress);
        return result.exitCode == 0
            ? (true, "PaddleOCR (GPU) uninstalled successfully.")
            : (false, $"Uninstall failed: {result.error}");
    }

    #endregion

    private async Task<(bool installed, string? version)> CheckPackageAsync(string venvPath, string packageName)
    {
        try
        {
            var pythonPath = GetVenvPythonPath(venvPath);
            var psi = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = $"-m pip show {packageName}",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            if (process == null) return (false, null);

            var output = await process.StandardOutput.ReadToEndAsync();
            await process.WaitForExitAsync();

            if (process.ExitCode == 0)
            {
                var match = Regex.Match(output, @"Version:\s*(.+)");
                return (true, match.Success ? match.Groups[1].Value.Trim() : "unknown");
            }
        }
        catch { }

        return (false, null);
    }

    private async Task<(int exitCode, string output, string error)> RunPipCommandAsync(
        string pythonPath, string args, Action<string>? onProgress = null)
    {
        var psi = new ProcessStartInfo
        {
            FileName = pythonPath,
            Arguments = $"-m pip {args}",
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };
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

        await process.WaitForExitAsync();

        return (process.ExitCode, output.ToString(), error.ToString());
    }

    private async Task<string> RunCommandAsync(string fileName, string args)
    {
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = fileName,
                Arguments = args,
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            if (process == null) return string.Empty;

            var output = await process.StandardOutput.ReadToEndAsync();
            await process.WaitForExitAsync();
            return output;
        }
        catch
        {
            return string.Empty;
        }
    }

    #region Python Install Manager

    /// <summary>
    /// Check if Python Install Manager (py.exe) is available
    /// </summary>
    public async Task<bool> IsPyInstallerAvailableAsync()
    {
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "py",
                Arguments = "--version",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            if (process == null) return false;

            await process.WaitForExitAsync();
            return process.ExitCode == 0;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Get list of installed Python versions using py list
    /// </summary>
    public async Task<List<PythonVersionInfo>> GetInstalledVersionsAsync()
    {
        var versions = new List<PythonVersionInfo>();

        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "py",
                Arguments = "list",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            if (process == null) return versions;

            var output = await process.StandardOutput.ReadToEndAsync();
            await process.WaitForExitAsync();

            if (process.ExitCode != 0) return versions;

            // Parse output: "  3.13.1    C:\Users\xxx\...\python.exe"
            // Active version starts with "*"
            var lines = output.Split('\n', StringSplitOptions.RemoveEmptyEntries);
            foreach (var line in lines.Skip(1)) // Skip header
            {
                var trimmed = line.Trim();
                if (string.IsNullOrEmpty(trimmed)) continue;

                var isActive = trimmed.StartsWith("*");
                if (isActive) trimmed = trimmed.Substring(1).Trim();

                var parts = trimmed.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length >= 1)
                {
                    var displayVersion = parts[0];
                    // Convert display format "3.14[-64]" to command tag "3.14" or "3.14-64"
                    var tag = displayVersion.Replace("[", "").Replace("]", "");
                    
                    versions.Add(new PythonVersionInfo
                    {
                        Version = displayVersion,
                        Tag = tag,
                        Path = parts.Length >= 2 ? parts[1] : "",
                        IsActive = isActive,
                        IsInstalled = true
                    });
                }
            }
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"GetInstalledVersionsAsync error: {ex.Message}");
        }

        return versions;
    }

    /// <summary>
    /// Get available Python versions for installation
    /// </summary>
    public List<string> GetAvailableVersions()
    {
        // Common Python versions available for installation
        return new List<string> { "3.14", "3.13", "3.12", "3.11", "3.10" };
    }

    /// <summary>
    /// Install a Python version using py install
    /// </summary>
    public async Task<(bool success, string message)> InstallPythonVersionAsync(
        string version, 
        Action<string>? onProgress = null)
    {
        try
        {
            onProgress?.Invoke($"Installing Python {version}...");

            var psi = new ProcessStartInfo
            {
                FileName = "py",
                Arguments = $"install {version}",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1";

            using var process = new Process { StartInfo = psi };
            var output = new StringBuilder();

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
                    output.AppendLine(e.Data);
                    onProgress?.Invoke(e.Data);
                }
            };

            process.Start();
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            await process.WaitForExitAsync();

            if (process.ExitCode == 0)
            {
                return (true, $"Python {version} installed successfully.");
            }
            else
            {
                return (false, $"Failed to install Python {version}. {output}");
            }
        }
        catch (Exception ex)
        {
            return (false, $"Error installing Python {version}: {ex.Message}");
        }
    }

    /// <summary>
    /// Uninstall a Python version using py uninstall
    /// </summary>
    public async Task<(bool success, string message)> UninstallPythonVersionAsync(
        string version,
        Action<string>? onProgress = null)
    {
        try
        {
            onProgress?.Invoke($"Uninstalling Python {version}...");

            var psi = new ProcessStartInfo
            {
                FileName = "py",
                Arguments = $"uninstall --yes {version}",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = new Process { StartInfo = psi };
            var output = new StringBuilder();

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
                    output.AppendLine(e.Data);
                    onProgress?.Invoke(e.Data);
                }
            };

            process.Start();
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            await process.WaitForExitAsync();

            if (process.ExitCode == 0)
            {
                return (true, $"Python {version} uninstalled successfully.");
            }
            else
            {
                return (false, $"Failed to uninstall Python {version}. {output}");
            }
        }
        catch (Exception ex)
        {
            return (false, $"Error uninstalling Python {version}: {ex.Message}");
        }
    }

    /// <summary>
    /// Set the active Python version and save to settings
    /// </summary>
    public async Task<(bool success, string message)> SetActiveVersionAsync(string version)
    {
        try
        {
            // Get the path for this specific version
            var psi = new ProcessStartInfo
            {
                FileName = "py",
                Arguments = $"-{version} -c \"import sys; print(sys.executable)\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            if (process == null) return (false, "Failed to start py command");

            var output = await process.StandardOutput.ReadToEndAsync();
            await process.WaitForExitAsync();

            if (process.ExitCode == 0 && !string.IsNullOrEmpty(output))
            {
                var pythonPath = output.Trim();
                _appState.SystemPythonPath = pythonPath;
                _appState.PythonVersion = version;
                await _appState.SaveAsync();
                return (true, $"Python {version} set as active. Path: {pythonPath}");
            }
            else
            {
                return (false, $"Failed to get Python {version} path");
            }
        }
        catch (Exception ex)
        {
            return (false, $"Error setting active version: {ex.Message}");
        }
    }

    #endregion
}

/// <summary>
/// Python version information
/// </summary>
public class PythonVersionInfo
{
    public string Version { get; set; } = "";  // Display version (e.g., "3.14[-64]")
    public string Tag { get; set; } = "";      // Command tag (e.g., "3.14" or "3.14-64")
    public string Path { get; set; } = "";
    public bool IsActive { get; set; }
    public bool IsInstalled { get; set; }
}
