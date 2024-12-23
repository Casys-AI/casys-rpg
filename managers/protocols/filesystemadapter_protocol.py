"""
FileSystem Adapter Protocol.
"""
from typing import Optional, List, Union, Protocol, runtime_checkable
from pathlib import Path
from config.storage_config import StorageConfig

@runtime_checkable
class FileSystemAdapterProtocol(Protocol):
    """Protocol for file system operations."""
    
    def __init__(self, config: StorageConfig) -> None:
        """Initialize with configuration."""
        ...

    def ensure_directory(self, path: Union[str, Path]) -> Path:
        """Create directory if it doesn't exist."""
        ...

    def write_file_async(self, path: Union[str, Path], content: str) -> None:
        """Write content to file asynchronously."""
        ...

    def read_file_async(self, path: Union[str, Path]) -> Optional[str]:
        """Read file content asynchronously."""
        ...

    def delete_file_async(self, path: Union[str, Path]) -> None:
        """Delete file asynchronously."""
        ...

    def list_files(self, directory: Union[str, Path], pattern: str = "*") -> List[Path]:
        """List files in directory matching pattern."""
        ...
