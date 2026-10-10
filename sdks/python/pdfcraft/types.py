"""Types and data models for the PdfCraft Python SDK (Issue #872).

# Architecture Reference
Module: sdks/python/pdfcraft/types.py
Purpose:
    Strongly typed dataclasses mirroring the Rust SDK domain models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union


@dataclass
class DocumentSource:
    """Input abstraction decoupling operations from raw filesystem paths."""

    path: Optional[Path] = None
    data: Optional[bytes] = None
    name: Optional[str] = None

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> DocumentSource:
        """Creates a DocumentSource referencing a local file path."""
        return cls(path=Path(path))

    @classmethod
    def from_bytes(cls, data: bytes, name: Optional[str] = None) -> DocumentSource:
        """Creates a DocumentSource referencing in-memory byte buffer."""
        return cls(data=data, name=name)


@dataclass
class DocumentResult:
    """Output abstraction representing in-memory or spilled file results."""

    data: Optional[bytes] = None
    path: Optional[Path] = None
    mime_type: str = "application/pdf"
    size_bytes: int = 0

    @property
    def is_memory(self) -> bool:
        """Returns True if the output is held in memory."""
        return self.data is not None

    @property
    def is_file(self) -> bool:
        """Returns True if the output was written to a file on disk."""
        return self.path is not None


@dataclass
class MergeOptions:
    """Configuration options for merging documents."""

    output_filename: Optional[str] = None
    pages: Optional[List[Optional[str]]] = None


@dataclass
class SplitResult:
    """Result of a document split operation."""

    files: List[Path] = field(default_factory=list)


@dataclass
class RenderOptions:
    """Configuration options for high-DPI page rendering."""

    dpi: float = 150.0
    image_format: str = "png"
