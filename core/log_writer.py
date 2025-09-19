"""
Enhanced logging system for Picture Finder with configurable output formats,
internationalization support, and performance metrics tracking.
"""

import datetime
import logging
import json
import os
import psutil
import sys
from typing import Optional, Dict, Any
from pathlib import Path


class PictureFinderLogger:
    """Enhanced logger with multiple output formats and i18n support."""
    
    def __init__(self, log_dir: str = ".", enable_console: bool = True, 
                 enable_json: bool = False, log_level: int = logging.INFO):
        """
        Initialize the logger with configurable options.
        
        Args:
            log_dir: Directory to store log files
            enable_console: Whether to output to console
            enable_json: Whether to create JSON log format
            log_level: Logging level (INFO, DEBUG, ERROR, etc.)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create timestamped log filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = self.log_dir / f"picture_finder_log_{timestamp}.txt"
        self.json_log_file = self.log_dir / f"picture_finder_log_{timestamp}.json" if enable_json else None
        
        # Set up logger
        self.logger = logging.getLogger('PictureFinder')
        self.logger.setLevel(log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = logging.Formatter('%(levelname)s: %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # Initialize session data
        self.session_data = {
            'session_start': datetime.datetime.now().isoformat(),
            'system_info': self._get_system_info(),
            'events': []
        }
        
        # Log session start
        self.log_info("Picture Finder session started")
        self.log_system_info()
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Collect system information for diagnostics."""
        try:
            memory = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            return {
                'python_version': sys.version,
                'platform': sys.platform,
                'cpu_count': cpu_count,
                'total_memory_gb': round(memory.total / (1024**3), 2),
                'available_memory_gb': round(memory.available / (1024**3), 2),
                'memory_percent': memory.percent
            }
        except Exception as e:
            return {'error': f"Could not collect system info: {str(e)}"}
    
    def log_system_info(self):
        """Log system information."""
        info = self.session_data['system_info']
        if 'error' not in info:
            self.log_info(f"System: {info['platform']}, "
                         f"CPU cores: {info['cpu_count']}, "
                         f"RAM: {info['total_memory_gb']}GB")
    
    def log_info(self, message: str, **kwargs):
        """Log an info message."""
        self.logger.info(message)
        self._add_json_event('INFO', message, kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log an error message."""
        self.logger.error(message)
        self._add_json_event('ERROR', message, kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log a warning message."""
        self.logger.warning(message)
        self._add_json_event('WARNING', message, kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log a debug message."""
        self.logger.debug(message)
        self._add_json_event('DEBUG', message, kwargs)
    
    def log_performance(self, operation: str, duration: float, **metrics):
        """Log performance metrics."""
        message = f"Performance - {operation}: {duration:.2f}s"
        if metrics:
            metric_str = ", ".join([f"{k}: {v}" for k, v in metrics.items()])
            message += f" ({metric_str})"
        
        self.log_info(message)
        self._add_json_event('PERFORMANCE', message, {
            'operation': operation,
            'duration_seconds': duration,
            **metrics
        })
    
    def log_file_operation(self, operation: str, source: str, destination: str = None, 
                          success: bool = True, error: str = None):
        """Log file operations."""
        if success:
            msg = f"File {operation}: {source}"
            if destination:
                msg += f" -> {destination}"
            self.log_info(msg)
        else:
            msg = f"File {operation} failed: {source}"
            if error:
                msg += f" - {error}"
            self.log_error(msg)
        
        self._add_json_event('FILE_OP', msg, {
            'operation': operation,
            'source': source,
            'destination': destination,
            'success': success,
            'error': error
        })
    
    def log_duplicate_group(self, hash_value: str, file_paths: list):
        """Log a group of duplicate files."""
        message = f"Duplicate group (hash: {hash_value[:16]}...): {len(file_paths)} files"
        self.log_info(message)
        self._add_json_event('DUPLICATES', message, {
            'hash': hash_value,
            'file_count': len(file_paths),
            'files': file_paths
        })
    
    def log_batch_progress(self, batch_num: int, total_batches: int, 
                          processed_files: int, total_files: int, eta_seconds: float = None):
        """Log batch processing progress."""
        progress_pct = (batch_num / total_batches) * 100
        message = f"Batch {batch_num}/{total_batches} ({progress_pct:.1f}%) - "
        message += f"Files: {processed_files}/{total_files}"
        
        if eta_seconds:
            eta_str = str(datetime.timedelta(seconds=int(eta_seconds)))
            message += f" - ETA: {eta_str}"
        
        self.log_info(message)
        self._add_json_event('PROGRESS', message, {
            'batch_current': batch_num,
            'batch_total': total_batches,
            'files_processed': processed_files,
            'files_total': total_files,
            'progress_percent': progress_pct,
            'eta_seconds': eta_seconds
        })
    
    def log_session_summary(self, **summary_data):
        """Log final session summary."""
        self.log_info("=== SESSION SUMMARY ===")
        for key, value in summary_data.items():
            self.log_info(f"{key.replace('_', ' ').title()}: {value}")
        
        self.session_data['session_end'] = datetime.datetime.now().isoformat()
        self.session_data['summary'] = summary_data
        
        # Write JSON log if enabled
        if self.json_log_file:
            self._write_json_log()
    
    def _add_json_event(self, event_type: str, message: str, data: dict):
        """Add event to JSON log data."""
        if self.json_log_file:
            event = {
                'timestamp': datetime.datetime.now().isoformat(),
                'type': event_type,
                'message': message,
                'data': data
            }
            self.session_data['events'].append(event)
    
    def _write_json_log(self):
        """Write JSON log file."""
        try:
            with open(self.json_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log_error(f"Failed to write JSON log: {str(e)}")
    
    def get_log_file_path(self) -> str:
        """Get the path to the main log file."""
        return str(self.log_file)


# Global logger instance
_logger_instance: Optional[PictureFinderLogger] = None


def create_log_file(log_dir: str = ".", **kwargs) -> str:
    """
    Create a new log file and return its path.
    
    Args:
        log_dir: Directory to store log files
        **kwargs: Additional arguments for PictureFinderLogger
    
    Returns:
        Path to the created log file
    """
    global _logger_instance
    _logger_instance = PictureFinderLogger(log_dir, **kwargs)
    return _logger_instance.get_log_file_path()


def get_logger() -> PictureFinderLogger:
    """Get the current logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = PictureFinderLogger()
    return _logger_instance


def log_message(log_file: str, message: str, level: str = 'INFO'):
    """
    Compatibility function for legacy code.
    
    Args:
        log_file: Log file path (ignored, uses global logger)
        message: Message to log
        level: Log level
    """
    logger = get_logger()
    
    if level.upper() == 'ERROR':
        logger.log_error(message)
    elif level.upper() == 'WARNING':
        logger.log_warning(message)
    elif level.upper() == 'DEBUG':
        logger.log_debug(message)
    else:
        logger.log_info(message)


# Convenience functions
def log_info(message: str, **kwargs):
    """Log an info message."""
    get_logger().log_info(message, **kwargs)


def log_error(message: str, **kwargs):
    """Log an error message."""
    get_logger().log_error(message, **kwargs)


def log_warning(message: str, **kwargs):
    """Log a warning message."""
    get_logger().log_warning(message, **kwargs)


def log_performance(operation: str, duration: float, **metrics):
    """Log performance metrics."""
    get_logger().log_performance(operation, duration, **metrics)


def log_file_operation(operation: str, source: str, destination: str = None, 
                      success: bool = True, error: str = None):
    """Log file operations."""
    get_logger().log_file_operation(operation, source, destination, success, error)


def log_session_summary(**summary_data):
    """Log session summary."""
    get_logger().log_session_summary(**summary_data)


def setup_logging(log_dir: str = "logs") -> str:
    """
    Set up application-wide logging.
    
    Args:
        log_dir: Directory to store log files
        
    Returns:
        Path to the log file
    """
    global _logger_instance
    
    # Ensure log directory exists
    Path(log_dir).mkdir(exist_ok=True)
    
    # Initialize logger with custom directory
    _logger_instance = PictureFinderLogger(log_dir=log_dir)
    
    # Return log file path
    return str(_logger_instance.log_file)


def create_log_file(log_dir: str = "logs") -> str:
    """
    Create a new log file (legacy compatibility function).
    
    Args:
        log_dir: Directory to store log files
        
    Returns:
        Path to the log file
    """
    return setup_logging(log_dir)