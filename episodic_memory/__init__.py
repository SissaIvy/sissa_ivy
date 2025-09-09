"""
Episodic Memory System (minimal, dependency-free)

This package provides:
- Robust JSON loader that extracts the last valid object from a mixed file
- In-memory store with simple vector embedding and retrieval
- Basic scoring that combines similarity, recency, and importance

Intended for demonstration and extension for production use.
"""

from __future__ import annotations

from .store import MemoryStore, RetrievalResult
from .utils import load_system_from_path
from .embeddings import get_embedder, HashEmbedder, OpenAIEmbedder
from .schema import load_schema, validate_instance

# Expose package version programmatically from installed metadata
try:  # Python 3.8+
    from importlib.metadata import PackageNotFoundError, version as _pkg_version  # type: ignore
except Exception:  # pragma: no cover
    try:  # fallback for very old environments
        from importlib_metadata import (  # type: ignore
            PackageNotFoundError,  # type: ignore
            version as _pkg_version,  # type: ignore
        )
    except Exception:  # pragma: no cover
        PackageNotFoundError = Exception  # type: ignore
        def _pkg_version(_name: str) -> str:  # type: ignore
            return "0.0.0+dev"


def _get_version() -> str:
    try:
        # Distribution name from pyproject: episodic-memory
        return _pkg_version("episodic-memory")
    except PackageNotFoundError:  # type: ignore
        # Editable/dev runs without installed metadata
        return "0.2.0+dev"


__version__ = _get_version()

__all__ = [
    "MemoryStore",
    "RetrievalResult",
    "load_system_from_path",
    "get_embedder",
    "HashEmbedder",
    "OpenAIEmbedder",
    "load_schema",
    "validate_instance",
    "__version__",
]
