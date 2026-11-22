"""Central configuration, read from environment variables with safe defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:  # Load a local .env file if python-dotenv is installed (it never overrides real env vars).
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:  # pragma: no cover
    pass

ROOT = Path(__file__).resolve().parents[1]


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Every value can be overridden with an environment variable."""

    persist_dir: Path
    sample_dir: Path
    collection_name: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    max_distance: float
    max_history_messages: int
    max_upload_mb: int
    groq_model: str
    gemini_model: str
    default_provider: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            persist_dir=Path(os.getenv("CHROMA_DIR", ROOT / "chroma_db")),
            sample_dir=Path(os.getenv("SAMPLE_POLICY_DIR", ROOT / "data" / "policies")),
            collection_name=os.getenv("COLLECTION_NAME", "company_policies"),
            chunk_size=_env_int("CHUNK_SIZE", 900),
            chunk_overlap=_env_int("CHUNK_OVERLAP", 150),
            top_k=_env_int("TOP_K", 5),
            # Cosine distance (0 = identical, 1 = unrelated). Chunks farther than this are dropped.
            max_distance=_env_float("MAX_DISTANCE", 0.80),
            max_history_messages=_env_int("MAX_HISTORY_MESSAGES", 6),
            max_upload_mb=_env_int("MAX_UPLOAD_MB", 20),
            groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            default_provider=os.getenv("LLM_PROVIDER", "groq").lower(),
        )
