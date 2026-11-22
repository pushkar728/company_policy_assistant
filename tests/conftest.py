"""Shared fixtures. Tests use a tiny deterministic embedder, so no model download is needed."""

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

import pytest

from policy_assistant.config import Settings
from policy_assistant.vectorstore import PolicyVectorStore

ROOT = Path(__file__).resolve().parents[1]
DIM = 512


class HashingEmbedding:
    """Bag-of-words hashing embedder (L2-normalised). Deterministic and dependency-free."""

    def __init__(self) -> None:
        pass

    @staticmethod
    def name() -> str:
        return "test-hashing-embedding"

    def get_config(self) -> dict:
        return {}

    @classmethod
    def build_from_config(cls, config: dict) -> "HashingEmbedding":
        return cls()

    def __call__(self, input: list[str]) -> list[list[float]]:  # noqa: A002 - Chroma's signature
        vectors = []
        for text in input:
            vec = [0.0] * DIM
            for token in re.findall(r"[a-z0-9]+", text.lower()):
                vec[int(hashlib.md5(token.encode()).hexdigest(), 16) % DIM] += 1.0
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            vectors.append([v / norm for v in vec])
        return vectors

    def embed_query(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        return self(input)


@pytest.fixture()
def settings(tmp_path) -> Settings:
    base = Settings.from_env()
    return Settings(**{**base.__dict__, "persist_dir": tmp_path / "chroma", "sample_dir": ROOT / "data" / "policies"})


@pytest.fixture()
def store(settings) -> PolicyVectorStore:
    return PolicyVectorStore(settings.persist_dir, "test_policies", embedding_function=HashingEmbedding())
