"""ChromaDB-backed vector store with per-document metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from .ingestion import Chunk


@dataclass(frozen=True)
class Source:
    """A retrieved chunk together with where it came from."""

    id: str
    file: str
    page: int
    text: str
    distance: float

    @property
    def relevance(self) -> float:
        """Cosine similarity clipped to [0, 1], for display."""
        return max(0.0, min(1.0, 1.0 - self.distance))


@dataclass(frozen=True)
class DocumentInfo:
    name: str
    chunks: int
    pages: int
    doc_hash: str


class PolicyVectorStore:
    """Thin wrapper around a persistent Chroma collection (cosine distance).

    By default embeddings come from Chroma's bundled all-MiniLM-L6-v2 ONNX model,
    which runs locally on CPU: no embedding API key and no PyTorch needed.
    """

    def __init__(
        self,
        persist_dir: str | Path,
        collection_name: str = "company_policies",
        embedding_function: Any | None = None,
    ) -> None:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function or embedding_functions.DefaultEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------ write
    def add_document(self, name: str, doc_hash: str, chunks: list[Chunk]) -> int:
        """Index a document, replacing any earlier version with the same file name."""
        if not chunks:
            return 0
        self.delete_document(name)
        batch = 100
        for start in range(0, len(chunks), batch):
            part = chunks[start : start + batch]
            self._collection.add(
                ids=[f"{doc_hash[:16]}-{c.index}" for c in part],
                documents=[c.text for c in part],
                metadatas=[
                    {"source": name, "page": c.page, "chunk": c.index, "doc_hash": doc_hash}
                    for c in part
                ],
            )
        return len(chunks)

    def delete_document(self, name: str) -> None:
        self._collection.delete(where={"source": name})

    # ------------------------------------------------------------------- read
    def count(self) -> int:
        return self._collection.count()

    def is_indexed(self, name: str, doc_hash: str) -> bool:
        found = self._collection.get(
            where={"$and": [{"source": name}, {"doc_hash": doc_hash}]}, limit=1
        )
        return bool(found["ids"])

    def list_documents(self) -> list[DocumentInfo]:
        data = self._collection.get(include=["metadatas"])
        grouped: dict[str, dict[str, Any]] = {}
        for meta in data["metadatas"] or []:
            entry = grouped.setdefault(
                meta["source"], {"chunks": 0, "pages": set(), "hash": meta.get("doc_hash", "")}
            )
            entry["chunks"] += 1
            entry["pages"].add(meta["page"])
        return [
            DocumentInfo(name=name, chunks=v["chunks"], pages=len(v["pages"]), doc_hash=v["hash"])
            for name, v in sorted(grouped.items())
        ]

    def query(
        self, text: str, k: int = 5, documents: list[str] | None = None
    ) -> list[Source]:
        """Return the ``k`` nearest chunks, optionally restricted to some files."""
        total = self.count()
        if total == 0 or not text.strip():
            return []

        where: dict[str, Any] | None = None
        if documents:
            where = {"source": documents[0]} if len(documents) == 1 else {"source": {"$in": documents}}

        result = self._collection.query(
            query_texts=[text],
            n_results=min(k, total),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        sources = []
        for chunk_id, doc, meta, dist in zip(
            result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]
        ):
            sources.append(
                Source(id=chunk_id, file=meta["source"], page=int(meta["page"]), text=doc, distance=float(dist))
            )
        return sources
