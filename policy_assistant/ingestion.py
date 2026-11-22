"""PDF text extraction and chunking.

Chunks never cross page boundaries, so every chunk carries an exact page number
that can be shown as a citation.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class IngestionError(Exception):
    """Raised when a document cannot be read or contains no extractable text."""


@dataclass(frozen=True)
class PageText:
    page: int  # 1-based
    text: str


@dataclass(frozen=True)
class Chunk:
    text: str
    page: int  # 1-based
    index: int  # position of the chunk within the whole document


def file_hash(data: bytes) -> str:
    """Stable content hash used to detect duplicate uploads."""
    return hashlib.sha256(data).hexdigest()


def clean_text(text: str) -> str:
    """Normalise whitespace left over from PDF extraction."""
    text = text.replace("\r", "\n").replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pages(data: bytes) -> list[PageText]:
    """Extract cleaned, non-empty pages from PDF bytes."""
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            # Many PDFs are "encrypted" with an empty user password.
            if not reader.decrypt(""):
                raise IngestionError("The PDF is password protected.")
        pages = []
        for number, page in enumerate(reader.pages, start=1):
            text = clean_text(page.extract_text() or "")
            if text:
                pages.append(PageText(page=number, text=text))
    except IngestionError:
        raise
    except (PdfReadError, ValueError, OSError, KeyError) as exc:
        raise IngestionError(f"Could not read the PDF: {exc}") from exc

    if not pages:
        raise IngestionError(
            "No text could be extracted. The PDF may be a scanned image (OCR is required)."
        )
    return pages


_UNIT_SPLIT = re.compile(r"(?<=[.!?;:])\s+|\n+")


def _split_units(text: str, size: int) -> list[str]:
    """Break text into sentence-like units, none longer than ``size``."""
    units: list[str] = []
    for raw in _UNIT_SPLIT.split(text):
        unit = raw.strip()
        while len(unit) > size:
            cut = unit.rfind(" ", 0, size)
            if cut < size // 2:
                cut = size
            units.append(unit[:cut].strip())
            unit = unit[cut:].strip()
        if unit:
            units.append(unit)
    return units


def split_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    """Greedily pack sentence units into chunks of at most ``chunk_size`` characters.

    Consecutive chunks share up to ``overlap`` characters of trailing context so an
    answer that straddles a boundary is still retrievable.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size")

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for unit in _split_units(text, chunk_size):
        added = len(unit) + (1 if current else 0)
        if current and current_len + added > chunk_size:
            chunks.append(" ".join(current))
            tail: list[str] = []
            tail_len = 0
            for previous in reversed(current):
                if tail_len + len(previous) + 1 > overlap:
                    break
                tail.insert(0, previous)
                tail_len += len(previous) + 1
            while tail and len(" ".join(tail)) + 1 + len(unit) > chunk_size:
                tail.pop(0)
            current = tail
            current_len = len(" ".join(current))
            added = len(unit) + (1 if current else 0)
        current.append(unit)
        current_len += added

    if current:
        chunks.append(" ".join(current))
    return chunks


def chunk_pages(pages: list[PageText], chunk_size: int = 900, overlap: int = 150) -> list[Chunk]:
    """Chunk every page, numbering chunks across the whole document."""
    chunks: list[Chunk] = []
    for page in pages:
        for text in split_text(page.text, chunk_size, overlap):
            chunks.append(Chunk(text=text, page=page.page, index=len(chunks)))
    return chunks
