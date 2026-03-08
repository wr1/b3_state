"""Utilities for file operations."""

from pathlib import Path


def get_file_mtime(path: Path) -> float:
    """Get modification time of a file."""
    return path.stat().st_mtime if path.exists() else 0.0


def is_file_non_empty(path: Path) -> bool:
    """Check if a file exists and is non-empty."""
    return path.exists() and path.stat().st_size > 0
