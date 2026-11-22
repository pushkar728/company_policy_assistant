"""High-level helpers that turn PDF files into indexed documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Settings
from .ingestion import IngestionError, chunk_pages, extract_pages, file_hash
from .vectorstore import PolicyVectorStore


@dataclass(frozen=True)
class IndexResult:
    name: str
    status: str  # "indexed" | "skipped" | "failed"
    chunks: int = 0
    message: str = ""


def index_bytes(
    store: PolicyVectorStore, name: str, data: bytes, settings: Settings
) -> IndexResult:
    """Index one PDF. Identical content that is already indexed is skipped."""
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        return IndexResult(name, "failed", message=f"File is larger than {settings.max_upload_mb} MB.")
    digest = file_hash(data)
    if store.is_indexed(name, digest):
        return IndexResult(name, "skipped", message="Already indexed.")
    try:
        pages = extract_pages(data)
    except IngestionError as exc:
        return IndexResult(name, "failed", message=str(exc))
    chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
    added = store.add_document(name, digest, chunks)
    return IndexResult(name, "indexed", chunks=added)


def index_directory(
    store: PolicyVectorStore, directory: Path, settings: Settings
) -> list[IndexResult]:
    """Index every PDF in ``directory``."""
    results = []
    for path in sorted(Path(directory).glob("*.pdf")):
        results.append(index_bytes(store, path.name, path.read_bytes(), settings))
    return results
