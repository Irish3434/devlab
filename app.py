#!/usr/bin/env python3
"""
Picture Finder - Main Application Entry Point

A comprehensive duplicate photo detection application with GUI interface,
performance optimization, and professional features.

Usage:
    python app.py

Features:
    - Perceptual hash-based duplicate detection
    - Modern GUI with accessibility support
    - Multi-threaded processing for performance
    - Automatic photo organization (copy/move modes)
    - Video file separation
    - ZIP export functionality
    - Comprehensive logging
    - Internationalization support
    - Settings persistence
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import logging
from typing import List, Tuple, Optional, Dict, Any

# Add the project root to Python path for imports
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    # Core imports
    from gui.interface import PictureFinderGUI
    from core.log_writer import get_logger, setup_logging
    from core.config import get_config
    
    # Optional imports for enhanced features
    try:
        import babel
        BABEL_AVAILABLE = True
    except ImportError:
        BABEL_AVAILABLE = False
    
    try:
        import ttkthemes
        THEMES_AVAILABLE = True
    except ImportError:
        THEMES_AVAILABLE = False

except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def check_dependencies() -> Tuple[bool, List[str], List[str]]:
    """
    Check if all required dependencies are available.
    
    Returns:
        tuple: (success: bool, missing_packages: list, missing_optional: list)
    """
    required_packages = [
        ('PIL', 'Pillow'),
        ('imagehash', 'imagehash'),
        ('tkinter', 'tkinter (built-in)'),
        ('pathlib', 'pathlib (built-in)')
    ]
    
    optional_packages = [
        ('ttkthemes', 'ttkthemes'),
        ('babel', 'babel'),
        ('psutil', 'psutil')
    ]
    
    missing = []
    
    # Check required packages
    for package, install_name in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(install_name)
    
    # Check optional packages (warnings only)
    missing_optional = []
    for package, install_name in optional_packages:
        try:
            __import__(package)
        except ImportError:
            missing_optional.append(install_name)
    
    return len(missing) == 0, missing, missing_optional


def setup_application_environment() -> bool:
    """
    Set up the application environment and create necessary directories.
    
    Returns:
        bool: True if setup successful, False otherwise
    """


def show_dependency_error(missing_packages: List[str], missing_optional: List[str]) -> None:
    """
    Display error message for missing dependencies.
    
    Args:
        missing_packages: List of missing required packages
        missing_optional: List of missing optional packages
    """


def setup_gui_environment() -> Optional[tk.Tk]:
    """
    Set up the GUI environment and return the root window.
    
    Returns:
        tk.Tk or None: Root window if successful, None if failed
    """


def main() -> None:
    """
    Main application entry point.
    
    Handles dependency checking, environment setup, and GUI initialization.
    """


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)