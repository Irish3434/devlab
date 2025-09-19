"""
Enhanced image processing system for Picture Finder with perceptual hashing,
duplicate detection, batch processing, and performance optimization.
"""

import os
import time
import hashlib
from collections import defaultdict
from multiprocessing import Pool, Manager, cpu_count
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import threading
from PIL import Image, ImageFile
import imagehash
from tqdm import tqdm
from typing import List, Tuple, Dict, Optional, Callable, Any
from pathlib import Path
import psutil
import gc

from core.file_manager import FileManager
from core.log_writer import get_logger


# Allow loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True


class PerformanceMonitor:
    """Monitor system performance and adjust processing parameters."""
    
    def __init__(self):
        self.cpu_percent_history = []
        self.memory_percent_history = []
        self.lock = Lock()
    
    def update_stats(self):
        """Update performance statistics."""
        with self.lock:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                
                self.cpu_percent_history.append(cpu_percent)
                self.memory_percent_history.append(memory.percent)
                
                # Keep only last 10 readings
                if len(self.cpu_percent_history) > 10:
                    self.cpu_percent_history.pop(0)
                    self.memory_percent_history.pop(0)
                    
            except Exception:
                pass  # Ignore errors in monitoring
    
    def get_avg_cpu_usage(self) -> float:
        """Get average CPU usage."""
        with self.lock:
            return sum(self.cpu_percent_history) / len(self.cpu_percent_history) if self.cpu_percent_history else 0
    
    def get_avg_memory_usage(self) -> float:
        """Get average memory usage."""
        with self.lock:
            return sum(self.memory_percent_history) / len(self.memory_percent_history) if self.memory_percent_history else 0
    
    def should_throttle(self, cpu_threshold: float = 90, memory_threshold: float = 85) -> bool:
        """Check if processing should be throttled."""
        return (self.get_avg_cpu_usage() > cpu_threshold or 
                self.get_avg_memory_usage() > memory_threshold)


class ImageHasher:
    """Enhanced image hasher with multiple algorithms and error handling."""
    
    HASH_ALGORITHMS = {
        'average': imagehash.average_hash,
        'perceptual': imagehash.phash,
        'difference': imagehash.dhash,
        'wavelet': imagehash.whash
    }
    
    def __init__(self, algorithm: str = 'average', hash_size: int = 8):
        """
        Initialize the hasher.
        
        Args:
            algorithm: Hash algorithm ('average', 'perceptual', 'difference', 'wavelet')
            hash_size: Size of the hash (default 8 for 64-bit hash)
        """
        self.algorithm = algorithm
        self.hash_size = hash_size
        self.hash_function = self.HASH_ALGORITHMS.get(algorithm, imagehash.average_hash)
        self.logger = get_logger()
    
    def hash_file(self, file_path: str, max_size: Tuple[int, int] = (1024, 1024)) -> Tuple[Optional[str], str, Dict[str, Any]]:
        """
        Calculate hash for a single image file with enhanced error handling.
        
        Args:
            file_path: Path to the image file
            max_size: Maximum image size for processing (width, height)
            
        Returns:
            Tuple of (hash_string, file_path, metadata)
        """
        metadata = {
            'file_size': 0,
            'image_size': (0, 0),
            'format': None,
            'error': None,
            'processing_time': 0
        }
        
        start_time = time.time()
        
        try:
            # Check if file exists and is readable
            path_obj = Path(file_path)
            if not path_obj.exists():
                metadata['error'] = 'File does not exist'
                return None, file_path, metadata
            
            metadata['file_size'] = path_obj.stat().st_size
            
            # Skip very large files that might cause memory issues
            if metadata['file_size'] > 100 * 1024 * 1024:  # 100MB
                metadata['error'] = 'File too large (>100MB)'
                return None, file_path, metadata
            
            # Open and process image
            with Image.open(file_path) as img:
                metadata['format'] = img.format
                metadata['image_size'] = img.size
                
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                elif img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Resize if image is too large
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Calculate hash
                hash_obj = self.hash_function(img, hash_size=self.hash_size)
                hash_string = str(hash_obj)
                
                metadata['processing_time'] = time.time() - start_time
                return hash_string, file_path, metadata
                
        except FileNotFoundError:
            metadata['error'] = 'File not found'
        except PermissionError:
            metadata['error'] = 'Permission denied'
        except Image.UnidentifiedImageError:
            metadata['error'] = 'Not a valid image file'
        except OSError as e:
            metadata['error'] = f'OS error: {str(e)}'
        except Exception as e:
            metadata['error'] = f'Unexpected error: {str(e)}'
        
        metadata['processing_time'] = time.time() - start_time
        return None, file_path, metadata


class DuplicateDetector:
    """Enhanced duplicate detection with configurable similarity and performance optimization."""
    
    def __init__(self, similarity_threshold: int = 10, hash_algorithm: str = 'average',
                 performance_mode: str = 'high'):
        """
        Initialize the duplicate detector.
        
        Args:
            similarity_threshold: Maximum Hamming distance for duplicates (1-20)
            hash_algorithm: Algorithm for hashing ('average', 'perceptual', etc.)
            performance_mode: 'low', 'medium', or 'high'
        """
        self.similarity_threshold = max(1, min(20, similarity_threshold))
        self.hash_algorithm = hash_algorithm
        self.performance_mode = performance_mode.lower()
        
        # Performance settings
        self.performance_settings = {
            'low': {'processes': 1, 'batch_size': 50, 'memory_limit': 0.5},
            'medium': {'processes': 2, 'batch_size': 200, 'memory_limit': 0.7},
            'high': {'processes': min(4, cpu_count()), 'batch_size': 500, 'memory_limit': 0.8}
        }
        
        self.settings = self.performance_settings.get(self.performance_mode, self.performance_settings['high'])
        self.hasher = ImageHasher(hash_algorithm)
        self.logger = get_logger()
        self.performance_monitor = PerformanceMonitor()
        
        # Progress tracking
        self.progress_callback: Optional[Callable] = None
        self.cancel_flag = threading.Event()
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Set callback for progress updates (current, total, message)."""
        self.progress_callback = callback
    
    def cancel_processing(self):
        """Cancel current processing operation."""
        self.cancel_flag.set()
        self.logger.log_info("Processing cancellation requested")
    
    def find_duplicates(self, folder_path: str, chunk_size: Optional[int] = None,
                       recursive: bool = False, file_extensions: Optional[List[str]] = None) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
        """
        Find duplicate images in a folder with enhanced performance and monitoring.
        
        Args:
            folder_path: Path to scan for images
            chunk_size: Override default batch size
            recursive: Scan subfolders recursively
            file_extensions: List of file extensions to process
            
        Returns:
            Tuple of (duplicate_groups, processing_stats)
        """
        start_time = time.time()
        self.cancel_flag.clear()
        
        # Initialize file manager and get file list
        file_manager = FileManager(recursive_scan=recursive)
        
        # Separate videos first
        self.logger.log_info(f"Starting duplicate detection in: {folder_path}")
        video_files = file_manager.separate_videos(folder_path)
        
        # Get image files
        if file_extensions is None:
            file_extensions = list(FileManager.IMAGE_EXTENSIONS)
        
        extensions_set = {ext.lower() for ext in file_extensions}
        image_files = file_manager.get_file_list(folder_path, extensions_set)
        
        # Remove files that were moved as videos
        video_paths = set(video_files)
        image_files = [f for f in image_files if str(f) not in video_paths]
        
        total_files = len(image_files)
        self.logger.log_info(f"Found {total_files} image files to process")
        
        if total_files == 0:
            return {}, {'total_files': 0, 'processing_time': time.time() - start_time}
        
        # Set batch size
        if chunk_size is None:
            chunk_size = self.settings['batch_size']
        
        # Adjust batch size based on available memory
        memory = psutil.virtual_memory()
        if memory.percent > 80:
            chunk_size = min(chunk_size, 50)
        
        # Process files in batches
        duplicates_map = defaultdict(list)
        processing_stats = {
            'total_files': total_files,
            'processed_files': 0,
            'errors': 0,
            'videos_separated': len(video_files),
            'processing_time': 0,
            'avg_time_per_file': 0,
            'memory_usage_mb': 0,
            'hash_algorithm': self.hash_algorithm,
            'similarity_threshold': self.similarity_threshold
        }
        
        # Create file batches
        file_batches = [
            image_files[i:i + chunk_size] 
            for i in range(0, len(image_files), chunk_size)
        ]
        
        self.logger.log_info(f"Processing {len(file_batches)} batches with {self.settings['processes']} processes")
        
        # Process batches
        for batch_idx, batch_files in enumerate(file_batches):
            if self.cancel_flag.is_set():
                self.logger.log_info("Processing cancelled by user")
                break
            
            batch_start_time = time.time()
            
            # Update performance monitor
            self.performance_monitor.update_stats()
            
            # Check if we should throttle
            if self.performance_monitor.should_throttle():
                self.logger.log_info("High system usage detected, throttling...")
                time.sleep(0.5)
            
            # Progress update
            if self.progress_callback:
                eta_seconds = None
                if batch_idx > 0:
                    elapsed = time.time() - start_time
                    rate = processing_stats['processed_files'] / elapsed
                    remaining_files = total_files - processing_stats['processed_files']
                    eta_seconds = remaining_files / rate if rate > 0 else None
                
                self.progress_callback(
                    processing_stats['processed_files'],
                    total_files,
                    f"Processing batch {batch_idx + 1}/{len(file_batches)}"
                )
                
                self.logger.log_batch_progress(
                    batch_idx + 1, len(file_batches),
                    processing_stats['processed_files'], total_files,
                    eta_seconds
                )
            
            # Process batch
            batch_results = self._process_batch(batch_files)
            
            # Group results
            for hash_str, file_path, metadata in batch_results:
                processing_stats['processed_files'] += 1
                
                if metadata.get('error'):
                    processing_stats['errors'] += 1
                    self.logger.log_error(f"Error processing {file_path}: {metadata['error']}")
                elif hash_str:
                    duplicates_map[hash_str].append(file_path)
            
            # Memory management
            if batch_idx % 10 == 0:
                gc.collect()
                memory_info = psutil.Process().memory_info()
                processing_stats['memory_usage_mb'] = memory_info.rss / (1024 * 1024)
            
            batch_time = time.time() - batch_start_time
            self.logger.log_performance(f"batch_{batch_idx + 1}", batch_time, files=len(batch_files))
            
            # Adaptive sleep based on performance mode
            if self.performance_mode == 'low':
                time.sleep(0.01)
        
        # Filter actual duplicates (groups with more than 1 file)
        duplicate_groups = {
            hash_str: file_list 
            for hash_str, file_list in duplicates_map.items() 
            if len(file_list) > 1
        }
        
        # Apply similarity threshold for near-duplicates
        if self.similarity_threshold > 0:
            duplicate_groups = self._apply_similarity_threshold(duplicate_groups)
        
        # Final statistics
        total_time = time.time() - start_time
        processing_stats['processing_time'] = total_time
        processing_stats['avg_time_per_file'] = total_time / max(1, processing_stats['processed_files'])
        processing_stats['duplicate_groups'] = len(duplicate_groups)
        processing_stats['total_duplicates'] = sum(len(group) for group in duplicate_groups.values())
        
        self.logger.log_info(f"Duplicate detection completed in {total_time:.2f}s")
        self.logger.log_info(f"Found {len(duplicate_groups)} groups containing {processing_stats['total_duplicates']} duplicates")
        
        return duplicate_groups, processing_stats
    
    def _process_batch(self, file_paths: List[Path]) -> List[Tuple[Optional[str], str, Dict[str, Any]]]:
        """Process a batch of files with multiprocessing or threading."""
        if self.settings['processes'] > 1 and len(file_paths) > 10:
            return self._process_batch_multiprocessing(file_paths)
        else:
            return self._process_batch_sequential(file_paths)
    
    def _process_batch_sequential(self, file_paths: List[Path]) -> List[Tuple[Optional[str], str, Dict[str, Any]]]:
        """Process batch sequentially."""
        results = []
        for file_path in file_paths:
            if self.cancel_flag.is_set():
                break
            result = self.hasher.hash_file(str(file_path))
            results.append(result)
        return results
    
    def _process_batch_multiprocessing(self, file_paths: List[Path]) -> List[Tuple[Optional[str], str, Dict[str, Any]]]:
        """Process batch using multiprocessing."""
        try:
            with Pool(processes=self.settings['processes']) as pool:
                # Convert paths to strings for pickling
                str_paths = [str(p) for p in file_paths]
                
                # Create multiple hasher instances for each process
                hashers = [ImageHasher(self.hash_algorithm) for _ in range(len(str_paths))]
                
                # Map work to processes
                results = pool.starmap(
                    ImageHasher.hash_file, 
                    [(hasher, path) for hasher, path in zip(hashers, str_paths)]
                )
                
                return results
                
        except Exception as e:
            self.logger.log_error(f"Multiprocessing failed, falling back to sequential: {str(e)}")
            return self._process_batch_sequential(file_paths)
    
    def _apply_similarity_threshold(self, duplicate_groups: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Apply similarity threshold to merge near-duplicate groups."""
        if self.similarity_threshold <= 0:
            return duplicate_groups
        
        self.logger.log_info(f"Applying similarity threshold: {self.similarity_threshold}")
        
        # Convert hash strings back to ImageHash objects for comparison
        hash_to_files = {}
        for hash_str, files in duplicate_groups.items():
            try:
                # Parse hash string back to ImageHash
                hash_obj = imagehash.hex_to_hash(hash_str)
                hash_to_files[hash_obj] = files
            except Exception as e:
                self.logger.log_error(f"Failed to parse hash {hash_str}: {str(e)}")
                continue
        
        # Group similar hashes
        processed_hashes = set()
        merged_groups = {}
        
        for hash1, files1 in hash_to_files.items():
            if hash1 in processed_hashes:
                continue
            
            # Start a new group
            group_files = files1.copy()
            group_hashes = {hash1}
            
            # Find similar hashes
            for hash2, files2 in hash_to_files.items():
                if hash2 in processed_hashes or hash2 == hash1:
                    continue
                
                try:
                    # Calculate Hamming distance
                    hamming_distance = hash1 - hash2
                    
                    if hamming_distance <= self.similarity_threshold:
                        group_files.extend(files2)
                        group_hashes.add(hash2)
                        
                except Exception as e:
                    self.logger.log_error(f"Error comparing hashes: {str(e)}")
                    continue
            
            # Mark all hashes in this group as processed
            processed_hashes.update(group_hashes)
            
            # Only keep groups with actual duplicates
            if len(group_files) > 1:
                # Use the first hash as the group key
                group_key = str(hash1)
                merged_groups[group_key] = group_files
        
        self.logger.log_info(f"Similarity grouping: {len(duplicate_groups)} -> {len(merged_groups)} groups")
        return merged_groups


class ImageProcessor:
    """Main image processor class combining all functionality."""
    
    def __init__(self, output_dir: str = ".", performance_mode: str = 'high',
                 hash_algorithm: str = 'average', similarity_threshold: int = 10):
        """
        Initialize the image processor.
        
        Args:
            output_dir: Output directory for processed files
            performance_mode: 'low', 'medium', or 'high'
            hash_algorithm: Hash algorithm to use
            similarity_threshold: Similarity threshold for duplicates
        """
        self.output_dir = output_dir
        self.file_manager = FileManager(output_dir)
        self.duplicate_detector = DuplicateDetector(
            similarity_threshold, hash_algorithm, performance_mode
        )
        self.logger = get_logger()
    
    def process_folder(self, folder_path: str, mode: str = 'copy', 
                      chunk_size: Optional[int] = None, recursive: bool = False,
                      export_zip: bool = False) -> Dict[str, Any]:
        """
        Complete folder processing workflow.
        
        Args:
            folder_path: Input folder path
            mode: 'copy' or 'move' for non-duplicates
            chunk_size: Batch size override
            recursive: Scan recursively
            export_zip: Create ZIP of unique photos
            
        Returns:
            Processing results and statistics
        """
        start_time = time.time()
        
        self.logger.log_info(f"Starting folder processing: {folder_path}")
        self.logger.log_info(f"Mode: {mode}, Recursive: {recursive}, Export ZIP: {export_zip}")
        
        # Find duplicates
        duplicate_groups, detection_stats = self.duplicate_detector.find_duplicates(
            folder_path, chunk_size, recursive
        )
        
        # Handle duplicates
        if duplicate_groups:
            processed_duplicates = self.file_manager.handle_duplicates(duplicate_groups)
        else:
            processed_duplicates = {}
        
        # Process non-duplicates
        self.logger.log_info("Processing non-duplicate files...")
        
        # Get all image files that aren't duplicates
        all_files = self.file_manager.get_file_list(folder_path, FileManager.IMAGE_EXTENSIONS)
        duplicate_files = set()
        for files in duplicate_groups.values():
            duplicate_files.update(files)
        
        non_duplicate_files = [f for f in all_files if str(f) not in duplicate_files]
        
        # Copy/move non-duplicates
        processed_unique = []
        for file_path in non_duplicate_files:
            result = self.file_manager.copy_or_move_with_timestamp(
                str(file_path), str(self.file_manager.unique_photos_dir), mode
            )
            if result:
                processed_unique.append(result)
        
        # Export to ZIP if requested
        zip_path = None
        if export_zip and self.file_manager.unique_photos_dir.exists():
            zip_path = self.file_manager.export_to_zip(
                str(self.file_manager.unique_photos_dir)
            )
        
        # Cleanup empty directories
        self.file_manager.cleanup_empty_directories(folder_path)
        
        # Compile final results
        total_time = time.time() - start_time
        
        results = {
            'processing_time': total_time,
            'detection_stats': detection_stats,
            'duplicate_groups': len(duplicate_groups),
            'total_duplicates': sum(len(group) for group in duplicate_groups.values()),
            'unique_files_processed': len(processed_unique),
            'zip_export_path': zip_path,
            'file_manager_stats': self.file_manager.get_statistics()
        }
        
        # Log final summary
        self.logger.log_session_summary(
            total_processing_time=f"{total_time:.2f}s",
            files_scanned=detection_stats['total_files'],
            duplicate_groups_found=results['duplicate_groups'],
            total_duplicates=results['total_duplicates'],
            unique_files_processed=results['unique_files_processed'],
            videos_separated=detection_stats['videos_separated'],
            errors=detection_stats['errors'] + self.file_manager.stats['errors']
        )
        
        return results
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Set progress callback for GUI updates."""
        self.duplicate_detector.set_progress_callback(callback)
    
    def cancel_processing(self):
        """Cancel current processing."""
        self.duplicate_detector.cancel_processing()


# Legacy compatibility functions
def find_duplicates(folder_path: str, threshold: int = 10, chunk_size: int = 500, 
                   processes: int = 4, mode: str = 'copy') -> str:
    """Legacy function for backward compatibility."""
    performance_mode = 'low' if processes == 1 else 'medium' if processes == 2 else 'high'
    
    processor = ImageProcessor(
        performance_mode=performance_mode,
        similarity_threshold=threshold
    )
    
    results = processor.process_folder(folder_path, mode, chunk_size)
    return processor.logger.get_log_file_path()


def hash_file(file_path: str) -> Tuple[Optional[str], str]:
    """Legacy function for backward compatibility."""
    hasher = ImageHasher()
    hash_result, path, metadata = hasher.hash_file(file_path)
    return hash_result, path