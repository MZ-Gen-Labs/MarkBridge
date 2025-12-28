#!/usr/bin/env python3
"""
Test Configuration for MarkBridge Python Tests
Provides common paths, helpers, and imports for test scripts.
"""

import os
import sys
from pathlib import Path

# Project paths
TESTS_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = TESTS_DIR.parent
RESOURCES_PYTHON = PROJECT_ROOT / "Resources" / "Python"
FIXTURES_DIR = TESTS_DIR / "Fixtures"
OUTPUT_DIR = TESTS_DIR / "Output"

# Add Resources/Python to path for importing main scripts
sys.path.insert(0, str(RESOURCES_PYTHON))

# Base app directory
LOCALAPPDATA = os.environ.get('LOCALAPPDATA', os.environ.get('USERPROFILE', ''))
if not LOCALAPPDATA:
    LOCALAPPDATA = str(Path.home() / "AppData" / "Local")

BASE_APP_DIR = Path(LOCALAPPDATA) / "MarkBridge"

# Production venv paths
MARKITDOWN_VENV = BASE_APP_DIR / ".venv_markitdown"
DOCLING_VENV = BASE_APP_DIR / ".venv_docling"
PADDLE_VENV = BASE_APP_DIR / ".venv_paddle"
MODELS_DIR = BASE_APP_DIR / "models"

# Test venv paths (isolated from production)
TEST_VENV_MARKITDOWN = BASE_APP_DIR / ".venv_test_markitdown"
TEST_VENV_DOCLING = BASE_APP_DIR / ".venv_test_docling"
TEST_VENV_PADDLE = BASE_APP_DIR / ".venv_test_paddle"


def get_production_venv(engine):
    """Get path to production venv for specified engine"""
    engine = engine.lower()
    if engine == "markitdown":
        return MARKITDOWN_VENV
    elif engine == "docling":
        return DOCLING_VENV
    elif engine in ("paddle", "paddleocr"):
        return PADDLE_VENV
    else:
        return DOCLING_VENV  # Default


def get_test_venv(engine):
    """Get path to test venv for specified engine"""
    engine = engine.lower()
    if engine == "markitdown":
        return TEST_VENV_MARKITDOWN
    elif engine == "docling":
        return TEST_VENV_DOCLING
    elif engine in ("paddle", "paddleocr"):
        return TEST_VENV_PADDLE
    else:
        return TEST_VENV_DOCLING  # Default


def get_test_python(engine):
    """Get path to python executable in test venv"""
    venv = get_test_venv(engine)
    if sys.platform == "win32":
        return venv / "Scripts" / "python.exe"
    else:
        return venv / "bin" / "python"


def get_production_python(engine):
    """Get path to python executable in production venv"""
    venv = get_production_venv(engine)
    if sys.platform == "win32":
        return venv / "Scripts" / "python.exe"
    else:
        return venv / "bin" / "python"


def ensure_output_dir():
    """Ensure Output directory exists"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR


def get_fixture(name):
    """Get path to a fixture file"""
    path = FIXTURES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return path


def print_header(title):
    """Print formatted section header"""
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print('=' * 50)


def print_result(ok, message):
    """Print test result"""
    status = "[OK]" if ok else "[FAILED]"
    print(f"  {status} {message}")


def check_venv(engine="docling", production=True):
    """Check if venv exists for specified engine"""
    if production:
        python_path = get_production_python(engine)
    else:
        python_path = get_test_python(engine)
    return python_path.exists()


# Info on import
if __name__ == "__main__":
    print(f"Tests Directory:    {TESTS_DIR}")
    print(f"Project Root:       {PROJECT_ROOT}")
    print(f"Resources/Python:   {RESOURCES_PYTHON}")
    print(f"Fixtures:           {FIXTURES_DIR}")
    print(f"Output:             {OUTPUT_DIR}")
    print(f"\nProduction Venvs:")
    for engine in ["markitdown", "docling", "paddle"]:
        venv = get_production_venv(engine)
        exists = "Yes" if check_venv(engine, True) else "No"
        print(f"  {engine:15} {venv} (exists: {exists})")
    print(f"\nTest Venvs:")
    for engine in ["markitdown", "docling", "paddle"]:
        venv = get_test_venv(engine)
        exists = "Yes" if check_venv(engine, False) else "No"
        print(f"  {engine:15} {venv} (exists: {exists})")
