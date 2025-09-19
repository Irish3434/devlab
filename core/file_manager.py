"""
Enhanced file management system for Picture Finder with secure operations,
video separation, timestamped naming, and comprehensive error handling.
"""

import os
import shutil
import datetime
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set
import mimetypes
import zipfile
from core.log_writer import get_logger


class FileManager:
    """Enhanced file manager with security, performance, and reliability features."""
    
    # Supported video extensions
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ogv'}
    
    # Supported image extensions
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.heic', '.heif'}
    
    # Large file threshold (50MB)
    LARGE_FILE_THRESHOLD = 50 * 1024 * 1024
    
    def __init__(self, base_output_dir: str = ".", recursive_scan: bool = False):
        """
        Initialize the file manager.
        
        Args:
            base_output_dir: Base directory for output folders
            recursive_scan: Whether to scan subfolders recursively
        """
        self.base_output_dir = Path(base_output_dir)
        self.recursive_scan = recursive_scan
        self.logger = get_logger()
        
        # Create output directories
        self.unique_photos_dir = self.base_output_dir / "unique_photos"
        self.videos_dir = self.base_output_dir / "videos"
        self.duplicates_dir = self.base_output_dir / "duplicates"
        
        # Statistics
        self.stats = {
            'videos_moved': 0,
            'duplicates_found': 0,
            'unique_photos_processed': 0,
            'errors': 0,
            'bytes_processed': 0
        }
        
        # Security: Track allowed directories
        self.allowed_dirs = set()
    
    def sanitize_path(self, path: str) -> Path:
        """
        Sanitize and validate file paths to prevent directory traversal.
        
        Args:
            path: Path to sanitize
            
        Returns:
            Sanitized Path object
            
        Raises:
            ValueError: If path is unsafe
        """
        try:
            # Resolve to absolute path and normalize
            sanitized = Path(path).resolve()
            
            # Check if path exists and is within allowed boundaries
            if not sanitized.exists():
                raise ValueError(f"Path does not exist: {path}")
            
            # Additional security: ensure path doesn't contain suspicious patterns
            path_str = str(sanitized)
            if '..' in path_str or path_str.startswith('/etc') or path_str.startswith('/sys'):
                raise ValueError(f"Unsafe path detected: {path}")
            
            return sanitized
            
        except Exception as e:
            raise ValueError(f"Invalid path: {path} - {str(e)}")
    
    def add_allowed_directory(self, directory: str):
        """Add a directory to the allowed list for security."""
        try:
            dir_path = self.sanitize_path(directory)
            self.allowed_dirs.add(dir_path)
            self.logger.log_info(f"Added allowed directory: {dir_path}")
        except ValueError as e:
            self.logger.log_error(f"Failed to add allowed directory: {str(e)}")
    
    def is_video_file(self, file_path: Path) -> bool:
        """
        Determine if a file is a video based on extension and size.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is considered a video
        """
        try:
            # Check extension
            if file_path.suffix.lower() in self.VIDEO_EXTENSIONS:
                return True
            
            # Check size threshold
            if file_path.stat().st_size > self.LARGE_FILE_THRESHOLD:
                # Try to determine MIME type
                mime_type, _ = mimetypes.guess_type(str(file_path))
                if mime_type and mime_type.startswith('video/'):
                    return True
                
                # Large files without clear image extension are likely videos
                if file_path.suffix.lower() not in self.IMAGE_EXTENSIONS:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.log_error(f"Error checking if file is video: {file_path} - {str(e)}")
            return False
    
    def is_image_file(self, file_path: Path) -> bool:
        """
        Determine if a file is an image.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is an image
        """
        try:
            # Check extension first
            if file_path.suffix.lower() in self.IMAGE_EXTENSIONS:
                return True
            
            # Check MIME type for files without clear extension
            mime_type, _ = mimetypes.guess_type(str(file_path))
            return mime_type and mime_type.startswith('image/')
            
        except Exception as e:
            self.logger.log_error(f"Error checking if file is image: {file_path} - {str(e)}")
            return False
    
    def separate_videos(self, source_folder: str) -> List[str]:
        """
        Separate video files from the source folder.
        
        Args:
            source_folder: Source folder path
            
        Returns:
            List of video files that were moved
        """
        self.logger.log_info(f"Starting video separation from: {source_folder}")
        
        try:
            source_path = self.sanitize_path(source_folder)
            self.add_allowed_directory(source_folder)
            
            # Create videos directory
            self.videos_dir.mkdir(exist_ok=True)
            
            moved_videos = []
            
            # Scan for files
            if self.recursive_scan:
                file_pattern = "**/*"
            else:
                file_pattern = "*"
            
            for file_path in source_path.glob(file_pattern):
                if not file_path.is_file():
                    continue
                
                if self.is_video_file(file_path):
                    try:
                        # Generate unique target path
                        target_path = self._get_unique_target_path(
                            self.videos_dir, file_path.name
                        )
                        
                        # Move video file
                        shutil.move(str(file_path), str(target_path))
                        moved_videos.append(str(file_path))
                        
                        self.stats['videos_moved'] += 1
                        self.stats['bytes_processed'] += target_path.stat().st_size
                        
                        self.logger.log_file_operation(
                            'video_move', str(file_path), str(target_path), True
                        )
                        
                    except Exception as e:
                        self.logger.log_file_operation(
                            'video_move', str(file_path), None, False, str(e)
                        )
                        self.stats['errors'] += 1
            
            self.logger.log_info(f"Video separation completed. Moved {len(moved_videos)} videos.")
            return moved_videos
            
        except Exception as e:
            self.logger.log_error(f"Video separation failed: {str(e)}")
            self.stats['errors'] += 1
            return []
    
    def copy_or_move_with_timestamp(self, source: str, dest_dir: str, 
                                  mode: str = 'copy', preserve_structure: bool = False) -> Optional[str]:
        """
        Copy or move file with timestamp to prevent overwrites.
        
        Args:
            source: Source file path
            dest_dir: Destination directory
            mode: 'copy' or 'move'
            preserve_structure: Whether to preserve directory structure
            
        Returns:
            Path to the copied/moved file, or None if failed
        """
        try:
            source_path = self.sanitize_path(source)
            dest_dir_path = Path(dest_dir)
            dest_dir_path.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped filename
            base_name = source_path.stem
            extension = source_path.suffix
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Add file hash for uniqueness
            file_hash = self._calculate_file_hash(source_path)[:8]
            new_name = f"{base_name}_{mode}_{timestamp}_{file_hash}{extension}"
            
            # Handle directory structure preservation
            if preserve_structure and len(source_path.parts) > 1:
                rel_dir = Path(*source_path.parts[:-1])
                target_dir = dest_dir_path / rel_dir
                target_dir.mkdir(parents=True, exist_ok=True)
                target_path = target_dir / new_name
            else:
                target_path = dest_dir_path / new_name
            
            # Perform operation
            if mode.lower() == 'move':
                shutil.move(str(source_path), str(target_path))
                operation = 'move'
            else:
                shutil.copy2(str(source_path), str(target_path))
                operation = 'copy'
            
            self.stats['unique_photos_processed'] += 1
            self.stats['bytes_processed'] += target_path.stat().st_size
            
            self.logger.log_file_operation(
                operation, str(source_path), str(target_path), True
            )
            
            return str(target_path)
            
        except Exception as e:
            self.logger.log_file_operation(
                mode, source, None, False, str(e)
            )
            self.stats['errors'] += 1
            return None
    
    def handle_duplicates(self, duplicate_groups: Dict[str, List[str]], 
                         keep_original: bool = True) -> Dict[str, List[str]]:
        """
        Handle duplicate files by moving them to duplicates folder.
        
        Args:
            duplicate_groups: Dictionary of hash -> list of file paths
            keep_original: Whether to keep one original in place
            
        Returns:
            Dictionary of processed duplicate groups
        """
        self.logger.log_info(f"Processing {len(duplicate_groups)} duplicate groups")
        
        # Create duplicates directory
        self.duplicates_dir.mkdir(exist_ok=True)
        
        processed_groups = {}
        
        for hash_value, file_paths in duplicate_groups.items():
            if len(file_paths) < 2:
                continue  # Not actually duplicates
            
            self.logger.log_duplicate_group(hash_value, file_paths)
            
            # Sort by modification time to keep the oldest
            sorted_files = sorted(
                file_paths, 
                key=lambda x: Path(x).stat().st_mtime if Path(x).exists() else 0
            )
            
            files_to_move = sorted_files[1:] if keep_original else sorted_files
            kept_file = sorted_files[0] if keep_original else None
            
            moved_files = []
            for duplicate_path in files_to_move:
                try:
                    source_path = Path(duplicate_path)
                    if not source_path.exists():
                        continue
                    
                    # Create subdirectory for this hash group
                    hash_dir = self.duplicates_dir / hash_value[:16]
                    hash_dir.mkdir(exist_ok=True)
                    
                    target_path = self._get_unique_target_path(
                        hash_dir, source_path.name
                    )
                    
                    shutil.move(str(source_path), str(target_path))
                    moved_files.append(str(target_path))
                    
                    self.logger.log_file_operation(
                        'duplicate_move', str(source_path), str(target_path), True
                    )
                    
                except Exception as e:
                    self.logger.log_file_operation(
                        'duplicate_move', duplicate_path, None, False, str(e)
                    )
                    self.stats['errors'] += 1
            
            processed_groups[hash_value] = {
                'kept_file': kept_file,
                'moved_files': moved_files,
                'total_duplicates': len(file_paths)
            }
            
            self.stats['duplicates_found'] += len(file_paths) - (1 if keep_original else 0)
        
        return processed_groups
    
    def export_to_zip(self, source_dir: str, zip_path: str = None, 
                     compression_level: int = 6, password: str = None) -> Optional[str]:
        """
        Export files to ZIP archive.
        
        Args:
            source_dir: Directory to zip
            zip_path: Output ZIP file path (auto-generated if None)
            compression_level: Compression level (0-9)
            password: Optional password protection
            
        Returns:
            Path to created ZIP file, or None if failed
        """
        try:
            source_path = Path(source_dir)
            if not source_path.exists():
                self.logger.log_error(f"Source directory does not exist: {source_dir}")
                return None
            
            # Generate ZIP filename if not provided
            if zip_path is None:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                zip_path = self.base_output_dir / f"unique_photos_{timestamp}.zip"
            else:
                zip_path = Path(zip_path)
            
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.log_info(f"Creating ZIP archive: {zip_path}")
            
            files_added = 0
            total_size = 0
            
            with zipfile.ZipFile(
                zip_path, 'w', 
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=compression_level
            ) as zipf:
                
                # Add password protection if requested
                if password:
                    zipf.setpassword(password.encode('utf-8'))
                
                # Add files recursively
                for file_path in source_path.rglob('*'):
                    if file_path.is_file():
                        # Calculate relative path for archive
                        rel_path = file_path.relative_to(source_path)
                        
                        zipf.write(file_path, rel_path)
                        files_added += 1
                        total_size += file_path.stat().st_size
                        
                        if files_added % 100 == 0:
                            self.logger.log_info(f"Added {files_added} files to ZIP...")
            
            zip_size = zip_path.stat().st_size
            compression_ratio = (1 - zip_size / total_size) * 100 if total_size > 0 else 0
            
            self.logger.log_info(
                f"ZIP export completed: {files_added} files, "
                f"Original: {total_size / (1024**2):.1f}MB, "
                f"Compressed: {zip_size / (1024**2):.1f}MB "
                f"({compression_ratio:.1f}% compression)"
            )
            
            return str(zip_path)
            
        except Exception as e:
            self.logger.log_error(f"ZIP export failed: {str(e)}")
            return None
    
    def get_file_list(self, folder_path: str, extensions: Set[str] = None) -> List[Path]:
        """
        Get list of files from folder with optional extension filtering.
        
        Args:
            folder_path: Folder to scan
            extensions: Set of allowed extensions (e.g., {'.jpg', '.png'})
            
        Returns:
            List of file paths
        """
        try:
            source_path = self.sanitize_path(folder_path)
            files = []
            
            if self.recursive_scan:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in source_path.glob(pattern):
                if not file_path.is_file():
                    continue
                
                # Filter by extension if specified
                if extensions and file_path.suffix.lower() not in extensions:
                    continue
                
                files.append(file_path)
            
            return files
            
        except Exception as e:
            self.logger.log_error(f"Failed to get file list: {str(e)}")
            return []
    
    def _get_unique_target_path(self, target_dir: Path, filename: str) -> Path:
        """Generate a unique target path to avoid overwrites."""
        target_path = target_dir / filename
        
        if not target_path.exists():
            return target_path
        
        # Add counter to make filename unique
        base_name = Path(filename).stem
        extension = Path(filename).suffix
        counter = 1
        
        while target_path.exists():
            new_name = f"{base_name}_{counter}{extension}"
            target_path = target_dir / new_name
            counter += 1
        
        return target_path
    
    def _calculate_file_hash(self, file_path: Path, algorithm: str = 'md5') -> str:
        """Calculate hash of a file for uniqueness."""
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            # Fallback to timestamp-based hash
            return str(int(datetime.datetime.now().timestamp()))
    
    def get_statistics(self) -> Dict[str, any]:
        """Get file operation statistics."""
        return self.stats.copy()
    
    def cleanup_empty_directories(self, directory: str):
        """Remove empty directories recursively."""
        try:
            dir_path = Path(directory)
            for path in sorted(dir_path.rglob('*'), reverse=True):
                if path.is_dir() and not any(path.iterdir()):
                    path.rmdir()
                    self.logger.log_info(f"Removed empty directory: {path}")
        except Exception as e:
            self.logger.log_error(f"Failed to cleanup empty directories: {str(e)}")


# Convenience functions for backward compatibility
def separate_videos(folder_path: str, log_file: str = None, recursive: bool = False) -> List[str]:
    """Legacy function for video separation."""
    file_manager = FileManager(recursive_scan=recursive)
    return file_manager.separate_videos(folder_path)


def copy_or_move_with_timestamp(source: str, dest_dir: str, mode: str = 'copy') -> Optional[str]:
    """Legacy function for file operations."""
    file_manager = FileManager()
    return file_manager.copy_or_move_with_timestamp(source, dest_dir, mode)