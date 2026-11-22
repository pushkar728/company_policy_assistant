"""Index PDFs into the vector store from the command line.

Usage:
    python scripts/ingest.py                 # index data/policies/
    python scripts/ingest.py path/to/folder  # index any folder of PDFs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy_assistant.config import Settings  # noqa: E402
from policy_assistant.indexer import index_directory  # noqa: E402
from policy_assistant.vectorstore import PolicyVectorStore  # noqa: E402


def main() -> int:
    settings = Settings.from_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=settings.sample_dir)
    args = parser.parse_args()

    if not args.directory.is_dir():
        print(f"Not a directory: {args.directory}")
        return 1
    store = PolicyVectorStore(settings.persist_dir, settings.collection_name)
    results = index_directory(store, args.directory, settings)
    if not results:
        print("No PDF files found.")
        return 1
    for r in results:
        detail = f"{r.chunks} chunks" if r.status == "indexed" else r.message
        print(f"[{r.status:>7}] {r.name} - {detail}")
    print(f"Total chunks in store: {store.count()}")
    return 0 if all(r.status != "failed" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
