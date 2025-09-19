"""
Configuration management system for Picture Finder with security and validation.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from core.log_writer import get_logger


@dataclass
class SecuritySettings:
    """Security-related settings."""
    validate_file_permissions: bool = True
    validate_file_types: bool = True
    allow_symlinks: bool = False
    max_file_size_mb: int = 100
    allowed_extensions: list = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']


@dataclass
class PerformanceSettings:
    """Performance-related settings."""
    hash_algorithm: str = 'average'
    similarity_threshold: int = 10
    performance_mode: str = 'high'
    enable_caching: bool = True
    max_cache_size: int = 1000
    chunk_size: int = 100
    max_threads: Optional[int] = None
    
    def __post_init__(self):
        if self.max_threads is None:
            import multiprocessing
            self.max_threads = max(2, multiprocessing.cpu_count() - 1)


@dataclass
class UISettings:
    """User interface settings."""
    theme: str = 'default'
    high_contrast_mode: bool = False
    enhanced_tooltips: bool = False
    window_width: int = 800
    window_height: int = 700
    remember_window_position: bool = True
    auto_save_settings: bool = True


@dataclass
class ProcessingSettings:
    """File processing settings."""
    recursive_scan: bool = False
    separate_videos: bool = True
    export_format: str = 'folders'  # 'folders' or 'zip'
    zip_compression_level: int = 6
    password_protect_zip: bool = False
    backup_originals: bool = False
    create_thumbnails: bool = False


class ConfigManager:
    """Configuration manager with validation and security features."""
    
    def __init__(self, config_file: str = "picture_finder_config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Configuration file path
        """
        self.config_file = Path(config_file)
        self.logger = get_logger()
        
        # Default settings
        self.security = SecuritySettings()
        self.performance = PerformanceSettings()
        self.ui = UISettings()
        self.processing = ProcessingSettings()
        
        # Load existing config if available
        self.load_config()
    
    def load_config(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if not self.config_file.exists():
                self.logger.log_info("No config file found, using defaults")
                return False
            
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Update settings from loaded data
            if 'security' in data:
                self.security = SecuritySettings(**data['security'])
            if 'performance' in data:
                self.performance = PerformanceSettings(**data['performance'])
            if 'ui' in data:
                self.ui = UISettings(**data['ui'])
            if 'processing' in data:
                self.processing = ProcessingSettings(**data['processing'])
            
            self.logger.log_info(f"Configuration loaded from {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Failed to load config: {str(e)}")
            return False
    
    def save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            config_data = {
                'security': asdict(self.security),
                'performance': asdict(self.performance),
                'ui': asdict(self.ui),
                'processing': asdict(self.processing),
                'version': '1.0.0',
                'last_saved': str(Path(__file__).stat().st_mtime)
            }
            
            # Create backup of existing config
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix('.json.bak')
                self.config_file.rename(backup_file)
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.log_info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Failed to save config: {str(e)}")
            return False
    
    def validate_settings(self) -> Dict[str, list]:
        """
        Validate all settings for potential issues.
        
        Returns:
            Dictionary of validation warnings/errors
        """
        issues = {
            'warnings': [],
            'errors': []
        }
        
        # Validate security settings
        if self.security.max_file_size_mb > 500:
            issues['warnings'].append("Very large max file size may cause memory issues")
        
        # Validate performance settings
        if self.performance.similarity_threshold < 0 or self.performance.similarity_threshold > 64:
            issues['errors'].append("Similarity threshold must be between 0 and 64")
        
        if self.performance.max_threads > 32:
            issues['warnings'].append("Very high thread count may degrade performance")
        
        # Validate UI settings
        if self.ui.window_width < 400 or self.ui.window_height < 300:
            issues['errors'].append("Window dimensions too small for proper display")
        
        return issues
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.security = SecuritySettings()
        self.performance = PerformanceSettings()
        self.ui = UISettings()
        self.processing = ProcessingSettings()
        self.logger.log_info("Configuration reset to defaults")
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary."""
        return {
            'security': asdict(self.security),
            'performance': asdict(self.performance),
            'ui': asdict(self.ui),
            'processing': asdict(self.processing)
        }
    
    def update_setting(self, category: str, key: str, value: Any) -> bool:
        """
        Update a specific setting.
        
        Args:
            category: Settings category ('security', 'performance', 'ui', 'processing')
            key: Setting key
            value: New value
            
        Returns:
            True if updated successfully
        """
        try:
            settings_obj = getattr(self, category, None)
            if settings_obj is None:
                self.logger.log_error(f"Unknown settings category: {category}")
                return False
            
            if hasattr(settings_obj, key):
                setattr(settings_obj, key, value)
                self.logger.log_info(f"Updated {category}.{key} = {value}")
                
                if self.ui.auto_save_settings:
                    self.save_config()
                
                return True
            else:
                self.logger.log_error(f"Unknown setting: {category}.{key}")
                return False
                
        except Exception as e:
            self.logger.log_error(f"Failed to update setting: {str(e)}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """
        Export configuration to a different location.
        
        Args:
            export_path: Path to export configuration
            
        Returns:
            True if exported successfully
        """
        try:
            original_config_file = self.config_file
            self.config_file = Path(export_path)
            
            result = self.save_config()
            
            # Restore original config file path
            self.config_file = original_config_file
            
            return result
            
        except Exception as e:
            self.logger.log_error(f"Failed to export config: {str(e)}")
            return False


# Global configuration instance
_config_manager = None

def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager