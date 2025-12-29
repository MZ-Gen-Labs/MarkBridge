<#
.SYNOPSIS
    MarkBridge - Docling Environment Setup Script
.DESCRIPTION
    Creates and configures a Python virtual environment for Docling.
    This script is used by both the main application and test environments
    to ensure consistent setup procedures.
.PARAMETER VenvPath
    Path where the virtual environment will be created
.PARAMETER PythonPath
    Path to the Python executable to use (e.g., py -3.12 or full path)
.PARAMETER Mode
    Installation mode: cpu, gpu, or nightly
.PARAMETER UseForkedDocling
    If specified, installs the forked version of Docling from MZ-Gen-Labs
.EXAMPLE
    .\Setup-DoclingVenv.ps1 -VenvPath "C:\venv\docling" -PythonPath "py -3.12" -Mode "nightly"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$VenvPath,
    
    [Parameter(Mandatory=$false)]
    [string]$PythonPath = "python",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("cpu", "gpu", "nightly")]
    [string]$Mode = "cpu",
    
    [Parameter(Mandatory=$false)]
    [switch]$UseForkedDocling
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[STEP] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Invoke-PipCommand {
    param(
        [string]$PythonPath,
        [string]$Arguments
    )
    
    Write-Host "  python -m pip $Arguments" -ForegroundColor Gray
    $process = Start-Process -FilePath $PythonPath -ArgumentList "-m pip $Arguments" -NoNewWindow -Wait -PassThru
    return $process.ExitCode
}

try {
    # Step 1: Create virtual environment
    Write-Step "Creating virtual environment at: $VenvPath"
    
    if (Test-Path $VenvPath) {
        Write-Host "  Removing existing venv..." -ForegroundColor Yellow
        Remove-Item $VenvPath -Recurse -Force
    }
    
    # Handle different Python path formats
    if ($PythonPath -like "py *") {
        $pyArgs = $PythonPath -replace "^py ", ""
        & py $pyArgs -m venv $VenvPath
    } else {
        & $PythonPath -m venv $VenvPath
    }
    
    if (-not (Test-Path "$VenvPath\Scripts\python.exe")) {
        throw "Failed to create virtual environment"
    }
    Write-Success "Virtual environment created"
    
    $venvPython = "$VenvPath\Scripts\python.exe"
    
    # Step 2: Upgrade pip
    Write-Step "Upgrading pip..."
    $exitCode = Invoke-PipCommand -PythonPath $venvPython -Arguments "install --upgrade pip"
    if ($exitCode -ne 0) { throw "Failed to upgrade pip" }
    Write-Success "pip upgraded"
    
    # Step 3: Install Docling
    Write-Step "Installing Docling..."
    if ($UseForkedDocling) {
        Write-Host "  Using forked version (MZ-Gen-Labs/docling)" -ForegroundColor Yellow
        $exitCode = Invoke-PipCommand -PythonPath $venvPython -Arguments "install git+https://github.com/MZ-Gen-Labs/docling.git"
    } else {
        $exitCode = Invoke-PipCommand -PythonPath $venvPython -Arguments "install docling"
    }
    if ($exitCode -ne 0) { throw "Failed to install Docling" }
    Write-Success "Docling installed"
    
    # Step 4: Install onnxruntime
    Write-Step "Installing onnxruntime..."
    $exitCode = Invoke-PipCommand -PythonPath $venvPython -Arguments "install onnxruntime"
    if ($exitCode -ne 0) { throw "Failed to install onnxruntime" }
    Write-Success "onnxruntime installed"
    
    # Step 5: Install CUDA support (if GPU or Nightly mode)
    if ($Mode -eq "gpu" -or $Mode -eq "nightly") {
        if ($Mode -eq "nightly") {
            Write-Step "Installing PyTorch Nightly (CUDA 12.8)..."
            $exitCode = Invoke-PipCommand -PythonPath $venvPython -Arguments "install --force-reinstall --pre torch --index-url https://download.pytorch.org/whl/nightly/cu128"
            if ($exitCode -ne 0) { throw "Failed to install PyTorch" }
            
            Write-Step "Installing torchvision..."
            $exitCode = Invoke-PipCommand -PythonPath $venvPython -Arguments "install --force-reinstall --pre torchvision --no-deps --index-url https://download.pytorch.org/whl/nightly/cu128"
            if ($exitCode -ne 0) { throw "Failed to install torchvision" }
        } else {
            Write-Step "Installing PyTorch (CUDA 12.4)..."
            $exitCode = Invoke-PipCommand -PythonPath $venvPython -Arguments "install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu124"
            if ($exitCode -ne 0) { throw "Failed to install PyTorch" }
        }
        Write-Success "CUDA support installed"
    }
    
    Write-Host ""
    Write-Success "Docling environment setup complete!"
    Write-Host "  Python: $((& $venvPython --version) 2>&1)" -ForegroundColor Gray
    $doclingVersion = (& $venvPython -m pip show docling 2>&1 | Select-String 'Version') -replace 'Version: ', ''
    Write-Host "  Docling: $doclingVersion" -ForegroundColor Gray
    
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
