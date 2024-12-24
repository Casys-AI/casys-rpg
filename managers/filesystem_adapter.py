"""
File System Adapter Module
Handles all file system operations through a unified interface.
"""

from typing import Dict, Optional, Any, List, Union
from datetime import datetime
import os
import json
from pathlib import Path
import asyncio
from loguru import logger

from config.storage_config import StorageConfig, StorageFormat
from managers.protocols.filesystemadapter_protocol import FileSystemAdapterProtocol
from models.errors_model import FileSystemError

class FileSystemAdapter(FileSystemAdapterProtocol):
    """
    Adapter for file system operations.
    Handles all low-level file system interactions.
    """

    def __init__(self, config: StorageConfig):
        """Initialize FileSystemAdapter with configuration."""
        self.config = config
        logger.info("Initializing FileSystemAdapter")
        
        try:
            # Create base directories
            self.base_dir = Path(config.base_path)
            logger.debug("Creating base directory: {}", self.base_dir.absolute())
            self.base_dir.mkdir(parents=True, exist_ok=True)
            
            # Create namespace directories (only non per_game)
            for namespace, ns_config in config.namespaces.items():
                if not ns_config.per_game:  # Skip per_game namespaces
                    path = self.base_dir / ns_config.path
                    logger.debug("Creating namespace directory for {}: {}", namespace, path.absolute())
                    path.mkdir(parents=True, exist_ok=True)
            
            logger.info("FileSystemAdapter initialized successfully")
            logger.debug("Base path: {}", self.base_dir.absolute())
            logger.debug("Encoding: {}", self.config.encoding)
            
        except Exception as e:
            logger.error("Error initializing filesystem: {}", str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to initialize filesystem: {str(e)}")

    def ensure_directory(self, path: Union[str, Path]) -> Path:
        """Create directory if it doesn't exist."""
        try:
            path = Path(path)
            logger.trace("Ensuring directory exists: {}", path.absolute())
            path.mkdir(parents=True, exist_ok=True)
            return path
        except Exception as e:
            logger.error("Error creating directory {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to create directory {path}: {str(e)}")

    async def write_file_async(self, path: Union[str, Path], content: str) -> None:
        """Write content to file asynchronously."""
        try:
            path = Path(path)
            logger.debug("Writing to file: {}", path.absolute())
            logger.trace("Content length: {} characters", len(content))
            
            # Validate path
            if not self.validate_path(path):
                logger.error("Invalid path: {} (outside base directory)", path.absolute())
                raise FileSystemError(f"Path {path} is outside the base directory")
            
            self.ensure_directory(path.parent)
            
            async with asyncio.Lock():
                logger.trace("Acquired lock for writing")
                await asyncio.to_thread(
                    self._write_file_sync, path, content
                )
                logger.debug("Successfully wrote to file: {}", path.absolute())
                
        except Exception as e:
            logger.error("Error writing to file {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to write to file {path}: {str(e)}")

    def _write_file_sync(self, path: Path, content: str) -> None:
        """Synchronous file write operation."""
        logger.trace("Starting synchronous write to: {}", path.absolute())
        with open(path, 'w', encoding=self.config.encoding) as f:
            f.write(content)
        logger.trace("Completed synchronous write")

    async def read_file_async(self, path: Union[str, Path]) -> Optional[str]:
        """Read file content asynchronously."""
        try:
            path = Path(path)
            logger.debug("Reading from file: {}", path.absolute())
            
            # Validate path
            if not self.validate_path(path):
                logger.error("Invalid path: {} (outside base directory)", path.absolute())
                raise FileSystemError(f"Path {path} is outside the base directory")
            
            if not path.exists():
                logger.debug("File does not exist: {}", path.absolute())
                return None
                
            async with asyncio.Lock():
                logger.trace("Acquired lock for reading")
                content = await asyncio.to_thread(
                    self._read_file_sync, path
                )
                
            logger.debug("Successfully read from file: {} ({} characters)", path.absolute(), len(content) if content else 0)
            return content
            
        except Exception as e:
            logger.error("Error reading file {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to read file {path}: {str(e)}")

    def _read_file_sync(self, path: Path) -> str:
        """Synchronous file read operation."""
        logger.trace("Starting synchronous read from: {}", path.absolute())
        with open(path, 'r', encoding=self.config.encoding) as f:
            content = f.read().strip()
        logger.trace("Completed synchronous read ({} characters)", len(content))
        return content

    async def delete_file_async(self, path: Union[str, Path]) -> None:
        """Delete file asynchronously."""
        try:
            path = Path(path)
            logger.debug("Deleting file: {}", path.absolute())
            
            # Validate path
            if not self.validate_path(path):
                logger.error("Invalid path: {} (outside base directory)", path.absolute())
                raise FileSystemError(f"Path {path} is outside the base directory")
            
            if path.exists():
                async with asyncio.Lock():
                    logger.trace("Acquired lock for deletion")
                    await asyncio.to_thread(path.unlink)
                    logger.debug("Successfully deleted file: {}", path.absolute())
            else:
                logger.debug("File does not exist: {}", path.absolute())
                
        except Exception as e:
            logger.error("Error deleting file {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to delete file {path}: {str(e)}")

    async def list_files(self, directory: Union[str, Path], pattern: str = "*") -> List[Path]:
        """List files in directory matching pattern."""
        try:
            directory = Path(directory)
            logger.debug("Listing files in directory: {} (pattern: {})", directory.absolute(), pattern)
            
            # Validate path
            if not self.validate_path(directory):
                logger.error("Invalid directory path: {} (outside base directory)", directory.absolute())
                raise FileSystemError(f"Directory {directory} is outside the base directory")
            
            if not directory.exists():
                logger.debug("Directory does not exist: {}", directory.absolute())
                return []
                
            async with asyncio.Lock():
                logger.trace("Acquired lock for directory listing")
                files = await asyncio.to_thread(
                    lambda: list(directory.glob(pattern))
                )
                
            sorted_files = sorted(files)
            logger.debug("Found {} files matching pattern '{}'", len(sorted_files), pattern)
            logger.trace("Files found: {}", [f.name for f in sorted_files])
            return sorted_files
            
        except Exception as e:
            logger.error("Error listing files in {}: {}", directory, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to list files in {directory}: {str(e)}")

    def get_file_info(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Get file information."""
        try:
            path = Path(path)
            logger.debug("Getting file info for: {}", path.absolute())
            
            # Validate path
            if not self.validate_path(path):
                logger.error("Invalid path: {} (outside base directory)", path.absolute())
                raise FileSystemError(f"Path {path} is outside the base directory")
            
            if not path.exists():
                logger.debug("File does not exist: {}", path.absolute())
                return {}
                
            stats = path.stat()
            info = {
                "size": stats.st_size,
                "created": datetime.fromtimestamp(stats.st_ctime),
                "modified": datetime.fromtimestamp(stats.st_mtime),
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "extension": path.suffix
            }
            logger.debug("File info retrieved: {}", info)
            return info
            
        except Exception as e:
            logger.error("Error getting file info for {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to get file info for {path}: {str(e)}")

    def validate_path(self, path: Union[str, Path]) -> bool:
        """Validate path is within allowed directories."""
        try:
            path = Path(path).resolve()
            base_path = self.base_dir.resolve()
            
            is_valid = str(path).startswith(str(base_path))
            logger.trace("Path validation: {} -> {}", path, "valid" if is_valid else "invalid")
            return is_valid
            
        except Exception as e:
            logger.error("Error validating path {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            return False

    def save_json(self, path: Union[str, Path], data: Dict[str, Any]) -> None:
        """Save data as JSON file."""
        try:
            path = Path(path)
            logger.debug("Saving JSON to file: {}", path.absolute())
            logger.trace("JSON data size: {} keys", len(data))
            
            # Validate path
            if not self.validate_path(path):
                logger.error("Invalid path: {} (outside base directory)", path.absolute())
                raise FileSystemError(f"Path {path} is outside the base directory")
            
            self.ensure_directory(path.parent)
            
            with open(path, 'w', encoding=self.config.encoding) as f:
                json.dump(data, f, indent=2)
                
            logger.debug("Successfully saved JSON to: {}", path.absolute())
            
        except Exception as e:
            logger.error("Error saving JSON to {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to save JSON to {path}: {str(e)}")

    def load_json(self, path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Load data from JSON file."""
        try:
            path = Path(path)
            logger.debug("Loading JSON from file: {}", path.absolute())
            
            # Validate path
            if not self.validate_path(path):
                logger.error("Invalid path: {} (outside base directory)", path.absolute())
                raise FileSystemError(f"Path {path} is outside the base directory")
            
            if not path.exists():
                logger.debug("JSON file does not exist: {}", path.absolute())
                return None
                
            with open(path, 'r', encoding=self.config.encoding) as f:
                data = json.load(f)
                
            logger.debug("Successfully loaded JSON from: {} ({} keys)", path.absolute(), len(data))
            return data
            
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in file {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Invalid JSON in file {path}: {str(e)}")
        except Exception as e:
            logger.error("Error loading JSON from {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to load JSON from {path}: {str(e)}")

    def save_markdown(self, path: Union[str, Path], content: str) -> None:
        """Save content as Markdown file."""
        try:
            path = Path(path)
            logger.debug("Saving Markdown to file: {}", path.absolute())
            logger.trace("Markdown content length: {} characters", len(content))
            
            # Validate path
            if not self.validate_path(path):
                logger.error("Invalid path: {} (outside base directory)", path.absolute())
                raise FileSystemError(f"Path {path} is outside the base directory")
            
            self.ensure_directory(path.parent)
            
            with open(path, 'w', encoding=self.config.encoding) as f:
                f.write(content)
                
            logger.debug("Successfully saved Markdown to: {}", path.absolute())
            
        except Exception as e:
            logger.error("Error saving Markdown to {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to save Markdown to {path}: {str(e)}")

    def load_markdown(self, path: Union[str, Path]) -> Optional[str]:
        """Load Markdown file content."""
        try:
            path = Path(path)
            logger.debug("Loading Markdown from file: {}", path.absolute())
            
            # Validate path
            if not self.validate_path(path):
                logger.error("Invalid path: {} (outside base directory)", path.absolute())
                raise FileSystemError(f"Path {path} is outside the base directory")
            
            if not path.exists():
                logger.debug("Markdown file does not exist: {}", path.absolute())
                return None
                
            with open(path, 'r', encoding=self.config.encoding) as f:
                content = f.read().strip()
                
            logger.debug("Successfully loaded Markdown from: {} ({} characters)", path.absolute(), len(content))
            return content
            
        except Exception as e:
            logger.error("Error loading Markdown from {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to load Markdown from {path}: {str(e)}")

    def list_markdown_files(self, directory: Union[str, Path], pattern: str = "*.md") -> List[Path]:
        """List all Markdown files in a directory."""
        try:
            directory = Path(directory)
            logger.debug("Listing Markdown files in directory: {} (pattern: {})", directory.absolute(), pattern)
            
            # Validate path
            if not self.validate_path(directory):
                logger.error("Invalid directory path: {} (outside base directory)", directory.absolute())
                raise FileSystemError(f"Directory {directory} is outside the base directory")
            
            if not directory.exists():
                logger.debug("Directory does not exist: {}", directory.absolute())
                return []
                
            return list(directory.glob(pattern))
            
        except Exception as e:
            logger.error("Error listing Markdown files in {}: {}", directory, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to list Markdown files in {directory}: {str(e)}")

    def get_session_path(self, base_dir: Union[str, Path]) -> Path:
        """Get or create session directory."""
        try:
            base_dir = Path(base_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = base_dir / timestamp
            
            self.ensure_directory(session_dir)
            return session_dir
        except Exception as e:
            logger.error("Error getting session path: {}", str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to get session path: {str(e)}")

    def clean_old_sessions(self, sessions_dir: Union[str, Path], max_sessions: int = None) -> None:
        """Clean old session directories."""
        try:
            if max_sessions is None:
                max_sessions = self.config.max_sessions
                
            sessions_dir = Path(sessions_dir)
            if not sessions_dir.exists():
                return

            # List all session directories
            sessions = sorted([
                d for d in sessions_dir.iterdir() 
                if d.is_dir() and d.name[0].isdigit()
            ], key=lambda x: x.stat().st_mtime, reverse=True)

            # Remove old sessions
            for session in sessions[max_sessions:]:
                try:
                    logger.info("Removing old session: {}", session)
                    self._remove_directory(session)
                except Exception as e:
                    logger.error("Error removing session {}: {}", session, str(e))
        except Exception as e:
            logger.error("Error cleaning old sessions: {}", str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to clean old sessions: {str(e)}")

    def read_file(self, path: Union[str, Path]) -> Optional[str]:
        """Read file content."""
        try:
            path = Path(path)
            logger.debug("Reading file: {}", path.absolute())
            
            # Validate path
            if not self.validate_path(path):
                logger.error("Invalid path: {} (outside base directory)", path.absolute())
                raise FileSystemError(f"Path {path} is outside the base directory")
            
            if not path.exists():
                logger.debug("File does not exist: {}", path.absolute())
                return None
                
            with open(path, 'r', encoding=self.config.encoding) as f:
                content = f.read()
                
            logger.debug("Successfully read file: {} ({} characters)", path.absolute(), len(content))
            return content
            
        except Exception as e:
            logger.error("Error reading file {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to read file {path}: {str(e)}")

    def write_file(self, path: Union[str, Path], content: str) -> None:
        """Write content to file."""
        try:
            path = Path(path)
            logger.debug("Writing to file: {}", path.absolute())
            logger.trace("Content length: {} characters", len(content))
            
            # Validate path
            if not self.validate_path(path):
                logger.error("Invalid path: {} (outside base directory)", path.absolute())
                raise FileSystemError(f"Path {path} is outside the base directory")
            
            self.ensure_directory(path.parent)
            
            with open(path, 'w', encoding=self.config.encoding) as f:
                f.write(content)
                
            logger.debug("Successfully wrote to file: {}", path.absolute())
            
        except Exception as e:
            logger.error("Error writing to file {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to write to file {path}: {str(e)}")

    def _remove_directory(self, path: Path) -> None:
        """Safely remove a directory and its contents."""
        try:
            for item in path.iterdir():
                if item.is_dir():
                    self._remove_directory(item)
                else:
                    item.unlink()
            path.rmdir()
        except Exception as e:
            logger.error("Error removing directory {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to remove directory {path}: {str(e)}")

    async def ensure_directory_async(self, path: Union[str, Path]) -> Path:
        """Create directory if it doesn't exist asynchronously."""
        try:
            path = Path(path)
            await asyncio.to_thread(os.makedirs, path, exist_ok=True)
            return path
        except Exception as e:
            logger.error("Error creating directory {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to create directory {path}: {str(e)}")

    async def save_json_async(self, path: Union[str, Path], data: Dict[str, Any]) -> None:
        """Save data as JSON file asynchronously."""
        try:
            path = Path(path)
            await self.ensure_directory_async(path.parent)
            
            await asyncio.to_thread(self.save_json, path, data)
        except Exception as e:
            logger.error("Error saving JSON to {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to save JSON to {path}: {str(e)}")

    async def load_json_async(self, path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Load JSON file asynchronously."""
        try:
            path = Path(path)
            if not path.exists():
                logger.debug("JSON file does not exist: {}", path.absolute())
                return None
                
            async def _load():
                return await asyncio.to_thread(self.load_json, path)
            return await _load()
        except Exception as e:
            logger.error("Error loading JSON from {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to load JSON from {path}: {str(e)}")

    async def get_session_path_async(self, base_dir: Optional[Path] = None) -> Path:
        """Get unique session path asynchronously."""
        try:
            if base_dir is None:
                base_dir = self.base_dir / "sessions"
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_path = base_dir / f"session_{timestamp}"
            await self.ensure_directory_async(session_path)
            return session_path
        except Exception as e:
            logger.error("Error getting session path: {}", str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to get session path: {str(e)}")

    async def clean_old_sessions_async(self, sessions_dir: Path, max_sessions: int = 5) -> None:
        """Clean old session directories asynchronously."""
        try:
            if not sessions_dir.exists():
                return
                
            # List and sort sessions by modification time
            sessions = sorted([
                d for d in sessions_dir.iterdir()
                if d.is_dir() and d.name.startswith("session_")
            ], key=lambda x: x.stat().st_mtime)
            
            # Remove oldest sessions if needed
            while len(sessions) > max_sessions:
                oldest = sessions.pop(0)
                await self.remove_directory_async(oldest)
                
        except Exception as e:
            logger.error("Error cleaning old sessions: {}", str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to clean old sessions: {str(e)}")

    async def remove_directory_async(self, path: Path) -> None:
        """Remove directory and contents asynchronously."""
        try:
            if not path.exists():
                return
                
            async def _remove():
                for item in path.iterdir():
                    if item.is_file():
                        os.remove(item)
                    elif item.is_dir():
                        await self.remove_directory_async(item)
                os.rmdir(path)
                
            await asyncio.to_thread(_remove)
            
        except Exception as e:
            logger.error("Error removing directory {}: {}", path, str(e))
            logger.error("Full error details:", exc_info=True)
            raise FileSystemError(f"Failed to remove directory {path}: {str(e)}")
