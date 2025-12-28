#!/usr/bin/env python3
"""
Test Venv Setup Script for MarkBridge
Creates isolated test virtual environments for each engine.

Usage:
    python setup_test_venv.py setup [--engine ENGINE] [--gpu]
    python setup_test_venv.py teardown [--engine ENGINE]
    python setup_test_venv.py status

Engines: markitdown, docling, paddle
"""

import os
import sys
import argparse
import subprocess
import shutil
from pathlib import Path

# Test venv configuration
LOCALAPPDATA = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
BASE_APP_DIR = Path(LOCALAPPDATA) / "MarkBridge"

TEST_VENVS = {
    "markitdown": BASE_APP_DIR / ".venv_test_markitdown",
    "docling": BASE_APP_DIR / ".venv_test_docling",
    "paddle": BASE_APP_DIR / ".venv_test_paddle",
}

# Package configurations (same as production)
PACKAGES = {
    "markitdown": ["markitdown[all]"],
    "docling": [
        "docling",
        "onnxruntime",
        "rapidocr_onnxruntime",
        "huggingface_hub",
        "PyYAML",
    ],
    "paddle": [
        "paddlepaddle",
        "paddleocr",
    ],
}


def get_python_path():
    """Get system Python path"""
    # Try common locations
    for path in ["python", "python3"]:
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return path
        except FileNotFoundError:
            pass
    
    # Try Windows Store Python
    if sys.platform == "win32":
        for ver in ["313", "312", "311", "310"]:
            path = Path(os.environ.get("LOCALAPPDATA", "")) / f"Microsoft/WindowsApps/python{ver}.exe"
            if path.exists():
                return str(path)
    
    return None


def create_venv(venv_path: Path, python_path: str = None):
    """Create a virtual environment"""
    if python_path is None:
        python_path = get_python_path()
    
    if python_path is None:
        print("Error: Python not found")
        return False
    
    print(f"Creating venv at: {venv_path}")
    
    try:
        result = subprocess.run(
            [python_path, "-m", "venv", str(venv_path)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Error creating venv: {result.stderr}")
            return False
        print("  Venv created successfully")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def install_packages(venv_path: Path, packages: list, gpu: bool = False):
    """Install packages in venv"""
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
    
    if not pip_path.exists():
        print(f"Error: pip not found at {pip_path}")
        return False
    
    # Upgrade pip first
    print("  Upgrading pip...")
    subprocess.run([str(pip_path), "install", "--upgrade", "pip"], capture_output=True)
    
    # Install packages
    for pkg in packages:
        print(f"  Installing {pkg}...")
        result = subprocess.run(
            [str(pip_path), "install", pkg],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"    Warning: Failed to install {pkg}")
            print(f"    {result.stderr[:200]}")
    
    return True


def delete_venv(venv_path: Path):
    """Delete a virtual environment"""
    if not venv_path.exists():
        print(f"Venv does not exist: {venv_path}")
        return True
    
    print(f"Deleting venv: {venv_path}")
    try:
        shutil.rmtree(venv_path)
        print("  Deleted successfully")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def check_venv_status(venv_path: Path):
    """Check if venv exists and is valid"""
    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"
    
    if python_path.exists():
        return "Ready"
    elif venv_path.exists():
        return "Invalid"
    else:
        return "Not Created"


def setup_engine(engine: str, gpu: bool = False):
    """Setup test venv for a specific engine"""
    if engine not in TEST_VENVS:
        print(f"Unknown engine: {engine}")
        return False
    
    venv_path = TEST_VENVS[engine]
    packages = PACKAGES.get(engine, [])
    
    print(f"\n{'='*50}")
    print(f" Setting up test venv for: {engine.upper()}")
    print('='*50)
    
    # Create venv
    if not create_venv(venv_path):
        return False
    
    # Install packages
    if packages:
        if not install_packages(venv_path, packages, gpu):
            return False
    
    print(f"\n[OK] Test venv for {engine} is ready")
    print(f"     Path: {venv_path}")
    return True


def teardown_engine(engine: str):
    """Teardown test venv for a specific engine"""
    if engine not in TEST_VENVS:
        print(f"Unknown engine: {engine}")
        return False
    
    venv_path = TEST_VENVS[engine]
    
    print(f"\n{'='*50}")
    print(f" Tearing down test venv for: {engine.upper()}")
    print('='*50)
    
    return delete_venv(venv_path)


def show_status():
    """Show status of all test venvs"""
    print(f"\n{'='*50}")
    print(" Test Venv Status")
    print('='*50)
    
    for engine, venv_path in TEST_VENVS.items():
        status = check_venv_status(venv_path)
        status_icon = {
            "Ready": "[OK]",
            "Invalid": "[!]",
            "Not Created": "[ ]"
        }.get(status, "[?]")
        print(f"  {status_icon} {engine:15} {status:12} {venv_path}")


def main():
    parser = argparse.ArgumentParser(description='Test Venv Setup for MarkBridge')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # setup command
    setup_parser = subparsers.add_parser('setup', help='Setup test venv')
    setup_parser.add_argument('--engine', choices=['markitdown', 'docling', 'paddle', 'all'],
                             default='all', help='Engine to setup')
    setup_parser.add_argument('--gpu', action='store_true', help='Install GPU packages')
    
    # teardown command
    teardown_parser = subparsers.add_parser('teardown', help='Teardown test venv')
    teardown_parser.add_argument('--engine', choices=['markitdown', 'docling', 'paddle', 'all'],
                                default='all', help='Engine to teardown')
    
    # status command
    subparsers.add_parser('status', help='Show test venv status')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        if args.engine == 'all':
            for engine in TEST_VENVS.keys():
                setup_engine(engine, args.gpu)
        else:
            setup_engine(args.engine, args.gpu)
    
    elif args.command == 'teardown':
        if args.engine == 'all':
            for engine in TEST_VENVS.keys():
                teardown_engine(engine)
        else:
            teardown_engine(args.engine)
    
    elif args.command == 'status':
        show_status()
    
    else:
        show_status()
        print("\nUse --help for usage information")


if __name__ == "__main__":
    main()
