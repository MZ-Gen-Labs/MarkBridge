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

# Venv paths
LOCALAPPDATA = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
DOCLING_VENV = Path(LOCALAPPDATA) / "MarkBridge" / ".venv_docling"
MODELS_DIR = Path(LOCALAPPDATA) / "MarkBridge" / "models"


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


def check_venv():
    """Check if Docling venv exists"""
    python_path = DOCLING_VENV / "Scripts" / "python.exe"
    return python_path.exists()


# Info on import
if __name__ == "__main__":
    print(f"Tests Directory:    {TESTS_DIR}")
    print(f"Project Root:       {PROJECT_ROOT}")
    print(f"Resources/Python:   {RESOURCES_PYTHON}")
    print(f"Fixtures:           {FIXTURES_DIR}")
    print(f"Output:             {OUTPUT_DIR}")
    print(f"Docling Venv:       {DOCLING_VENV}")
    print(f"Venv Exists:        {check_venv()}")
