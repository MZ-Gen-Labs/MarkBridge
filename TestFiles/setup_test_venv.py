#!/usr/bin/env python3
"""
Setup Test Virtual Environment for RapidOCR v5 Testing
Creates an isolated venv and installs all required packages.
"""

import os
import sys
import subprocess
import venv

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_NAME = ".venv_test"
VENV_PATH = os.path.join(SCRIPT_DIR, VENV_NAME)

# Required packages for RapidOCR v5
PACKAGES = [
    "rapidocr_onnxruntime",
    "huggingface_hub",
    "pymupdf",
    "pyyaml",
    "opencv-python-headless",
    "numpy"
]


def print_step(msg, status="..."):
    """Print a step with status"""
    print(f"  {msg}: {status}")


def get_python_executable():
    """Get the Python executable in venv"""
    if sys.platform == "win32":
        return os.path.join(VENV_PATH, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_PATH, "bin", "python")


def get_pip_executable():
    """Get the pip executable in venv"""
    if sys.platform == "win32":
        return os.path.join(VENV_PATH, "Scripts", "pip.exe")
    else:
        return os.path.join(VENV_PATH, "bin", "pip")


def create_venv():
    """Create virtual environment"""
    print("\n[Phase 1] Creating Virtual Environment")
    print(f"  Path: {VENV_PATH}")
    
    if os.path.exists(VENV_PATH):
        print("  Status: Already exists, skipping creation")
        return True
    
    try:
        print("  Creating venv...")
        venv.create(VENV_PATH, with_pip=True)
        print("  Status: Created successfully")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False


def upgrade_pip():
    """Upgrade pip in venv"""
    print("\n[Phase 2] Upgrading pip")
    python = get_python_executable()
    
    try:
        result = subprocess.run(
            [python, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("  Status: OK")
            return True
        else:
            print(f"  Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def install_packages():
    """Install required packages"""
    print("\n[Phase 3] Installing Packages")
    pip = get_pip_executable()
    
    for pkg in PACKAGES:
        print(f"  Installing {pkg}...", end="", flush=True)
        try:
            result = subprocess.run(
                [pip, "install", pkg],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(" OK")
            else:
                print(f" FAILED")
                print(f"    Error: {result.stderr[:200]}")
                return False
        except Exception as e:
            print(f" FAILED: {e}")
            return False
    
    return True


def verify_installation():
    """Verify all packages are installed correctly"""
    print("\n[Phase 4] Verification")
    python = get_python_executable()
    
    checks = [
        ("rapidocr_onnxruntime", "from rapidocr_onnxruntime import RapidOCR; print('OK')"),
        ("huggingface_hub", "import huggingface_hub; print('OK')"),
        ("pymupdf", "import fitz; print('OK')"),
        ("pyyaml", "import yaml; print('OK')"),
        ("opencv", "import cv2; print('OK')"),
        ("numpy", "import numpy; print('OK')"),
    ]
    
    all_ok = True
    for name, code in checks:
        print(f"  {name}...", end="", flush=True)
        try:
            result = subprocess.run(
                [python, "-c", code],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and "OK" in result.stdout:
                print(" OK")
            else:
                print(f" FAILED")
                print(f"    {result.stderr[:100]}")
                all_ok = False
        except Exception as e:
            print(f" FAILED: {e}")
            all_ok = False
    
    return all_ok


def print_next_steps():
    """Print instructions for next steps"""
    python = get_python_executable()
    print("\n" + "=" * 50)
    print("Setup Complete!")
    print("=" * 50)
    print("\nNext step - run the test script:")
    print(f'  {python} test_rapidocr_v5.py')


def main():
    print("=" * 50)
    print("RapidOCR v5 Test Environment Setup")
    print("=" * 50)
    
    # Step 1: Create venv
    if not create_venv():
        print("\nSetup failed at venv creation.")
        sys.exit(1)
    
    # Step 2: Upgrade pip
    if not upgrade_pip():
        print("\nSetup failed at pip upgrade.")
        sys.exit(1)
    
    # Step 3: Install packages
    if not install_packages():
        print("\nSetup failed at package installation.")
        sys.exit(1)
    
    # Step 4: Verify
    if not verify_installation():
        print("\nSetup failed at verification.")
        sys.exit(1)
    
    print_next_steps()


if __name__ == "__main__":
    main()
