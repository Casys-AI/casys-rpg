"""
FileSystem Adapter Protocol.
"""
from typing import Protocol, Union, Optional, List
from typing import runtime_checkable
from pathlib import Path

from config.storage_config import StorageConfig

@runtime_checkable
class FileSystemAdapterProtocol(Protocol):
    """Protocol for file system operations."""
    
    def __init__(self, config: StorageConfig):
        """Initialize with configuration."""
        ...

    def ensure_directory(self, path: Union[str, Path]) -> Path:
        """Create directory if it doesn't exist."""
        ...

    async def write_file_async(self, path: Union[str, Path], content: str) -> None:
        """Write content to file asynchronously."""
        ...

    async def read_file_async(self, path: Union[str, Path]) -> Optional[str]:
        """Read file content asynchronously."""
        ...

    async def delete_file_async(self, path: Union[str, Path]) -> None:
        """Delete file asynchronously."""
        ...

    async def list_files(self, directory: Union[str, Path], pattern: str = "*") -> List[Path]:
        """List files in directory matching pattern."""
        ...
