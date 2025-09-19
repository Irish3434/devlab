"""
Async file operations for Picture Finder using aiofiles.
Provides non-blocking file I/O operations for improved performance.
"""

import asyncio
import aiofiles
from pathlib import Path
from typing import List, Optional, Dict, Any
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import functools

from core.log_writer import get_logger


class AsyncFileManager:
    """Async file manager for non-blocking operations."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.logger = get_logger()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def async_copy_file(self, src: str, dst: str) -> bool:
        """Asynchronously copy a file."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                functools.partial(shutil.copy2, src, dst)
            )
            return True
        except Exception as e:
            self.logger.log_error(f"Async copy failed: {src} -> {dst}", error=str(e))
            return False

    async def async_move_file(self, src: str, dst: str) -> bool:
        """Asynchronously move a file."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                functools.partial(shutil.move, src, dst)
            )
            return True
        except Exception as e:
            self.logger.log_error(f"Async move failed: {src} -> {dst}", error=str(e))
            return False

    async def async_read_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Asynchronously read file information."""
        try:
            loop = asyncio.get_event_loop()
            stat_result = await loop.run_in_executor(
                self.executor,
                os.stat,
                file_path
            )

            return {
                'size': stat_result.st_size,
                'mtime': stat_result.st_mtime,
                'path': file_path,
                'exists': True
            }
        except Exception as e:
            self.logger.log_error(f"Failed to read file info: {file_path}", error=str(e))
            return None

    async def async_create_directory(self, path: str) -> bool:
        """Asynchronously create directory."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                functools.partial(os.makedirs, path, exist_ok=True)
            )
            return True
        except Exception as e:
            self.logger.log_error(f"Failed to create directory: {path}", error=str(e))
            return False

    async def batch_process_files(self, operations: List[Dict[str, Any]]) -> List[bool]:
        """Process multiple file operations asynchronously."""
        tasks = []

        for op in operations:
            if op['type'] == 'copy':
                task = self.async_copy_file(op['src'], op['dst'])
            elif op['type'] == 'move':
                task = self.async_move_file(op['src'], op['dst'])
            else:
                continue
            tasks.append(task)

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to False
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(False)
            else:
                processed_results.append(result)

        return processed_results

    def shutdown(self):
        """Shutdown the executor."""
        self.executor.shutdown(wait=True)


# Global async file manager instance
_async_file_manager: Optional[AsyncFileManager] = None


def get_async_file_manager() -> AsyncFileManager:
    """Get or create global async file manager instance."""
    global _async_file_manager
    if _async_file_manager is None:
        _async_file_manager = AsyncFileManager()
    return _async_file_manager


async def async_file_operation(operation: str, src: str, dst: str) -> bool:
    """Convenience function for async file operations."""
    manager = get_async_file_manager()

    if operation == 'copy':
        return await manager.async_copy_file(src, dst)
    elif operation == 'move':
        return await manager.async_move_file(src, dst)
    else:
        return False