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

# Add the project root to Python path for imports
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    # Core imports
    from gui.interface import PictureFinderGUI
    from core.log_writer import setup_logging, get_logger
    
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


def check_dependencies():
    """
    Check if all required dependencies are available.
    
    Returns:
        tuple: (success: bool, missing_packages: list)
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


def setup_application_environment():
    """Set up the application environment and logging."""
    # Ensure output directories exist
    output_dirs = ['logs', 'duplicates', 'unique_photos', 'videos']
    
    for dir_name in output_dirs:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
    
    # Set up logging
    log_file = setup_logging()
    logger = get_logger()
    
    logger.log_info("Picture Finder application starting")
    logger.log_info(f"Python version: {sys.version}")
    logger.log_info(f"Working directory: {os.getcwd()}")
    logger.log_info(f"Log file: {log_file}")
    
    return logger


def show_dependency_error(missing_packages, missing_optional):
    """Show error dialog for missing dependencies."""
    message = "Missing Required Dependencies:\n\n"
    
    if missing_packages:
        message += "Required packages:\n"
        for package in missing_packages:
            message += f"  • {package}\n"
        message += "\nPlease install with:\n"
        message += "pip install -r requirements.txt\n\n"
    
    if missing_optional:
        message += "Optional packages (recommended):\n"
        for package in missing_optional:
            message += f"  • {package}\n"
        message += "\nThese packages provide enhanced features but are not required.\n"
    
    # Try to show GUI error, fallback to console
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        messagebox.showerror("Dependency Error", message)
        root.destroy()
    except Exception:
        print("DEPENDENCY ERROR:")
        print(message)


def setup_gui_environment():
    """Set up the GUI environment and handle platform-specific settings."""
    # Create root window
    root = tk.Tk()
    
    # Platform-specific adjustments
    if sys.platform == "darwin":  # macOS
        try:
            # Enable high-DPI support on macOS
            root.tk.call('tk', 'scaling', 2.0)
        except Exception:
            pass
    
    elif sys.platform.startswith("win"):  # Windows
        try:
            # Enable DPI awareness on Windows
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    
    # Set window properties
    root.title("Picture Finder")
    
    # Center window on screen
    root.update_idletasks()
    width = 800
    height = 700
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    return root


def main():
    """Main application entry point."""
    # Check dependencies first
    deps_ok, missing_required, missing_optional = check_dependencies()
    
    if not deps_ok:
        show_dependency_error(missing_required, missing_optional)
        return 1
    
    # Warn about missing optional packages
    if missing_optional:
        print("Warning: Optional packages missing:")
        for package in missing_optional:
            print(f"  - {package}")
        print("Some features may be limited. Install with:")
        print("pip install " + " ".join(missing_optional))
        print()
    
    try:
        # Set up application environment
        logger = setup_application_environment()
        
        # Log system information
        logger.log_info(f"Operating System: {sys.platform}")
        logger.log_info(f"Python executable: {sys.executable}")
        
        if missing_optional:
            logger.log_warning(f"Missing optional packages: {', '.join(missing_optional)}")
        
        # Set up GUI
        root = setup_gui_environment()
        
        # Create and run application
        logger.log_info("Initializing GUI...")
        app = PictureFinderGUI(root)
        
        logger.log_info("Starting main event loop")
        root.mainloop()
        
        logger.log_info("Application closed normally")
        return 0
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 130
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"ERROR: {error_msg}")
        
        # Try to log the error
        try:
            logger = get_logger()
            logger.log_error(error_msg)
        except Exception:
            pass
        
        # Show error dialog if possible
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Application Error",
                f"An unexpected error occurred:\n\n{error_msg}\n\n"
                "Check the log file for more details."
            )
            root.destroy()
        except Exception:
            pass
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)