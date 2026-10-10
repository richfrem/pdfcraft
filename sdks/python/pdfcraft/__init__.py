"""PdfCraft Python SDK (Issue #872).

# Architecture Reference
Module: sdks/python/pdfcraft/__init__.py
Purpose:
    Public package exports for the unified PdfCraft Python client.
"""

from pdfcraft.errors import (
    ConflictError,
    InvalidArgumentError,
    NotFoundError,
    PdfCraftError,
    ProblemDetails,
    QuotaExceededError,
)
from pdfcraft.local import LocalClient
from pdfcraft.rest import RestClient
from pdfcraft.types import (
    DocumentResult,
    DocumentSource,
    MergeOptions,
    RenderOptions,
    SplitResult,
)

__all__ = [
    "ConflictError",
    "DocumentResult",
    "DocumentSource",
    "InvalidArgumentError",
    "LocalClient",
    "MergeOptions",
    "NotFoundError",
    "PdfCraftError",
    "ProblemDetails",
    "QuotaExceededError",
    "RenderOptions",
    "RestClient",
    "SplitResult",
]
