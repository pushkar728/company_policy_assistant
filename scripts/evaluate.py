"""Measure retrieval quality on a labelled question set (no LLM key needed).

For each question we check whether the expected policy file appears in the top-k
results (source hit) and whether the expected fact appears in the retrieved text
(answer hit). Prints hit rates and mean reciprocal rank (MRR).

Usage:
    python scripts/evaluate.py
    python scripts/evaluate.py --k 3 --questions data/eval_questions.json
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policy_assistant.config import ROOT, Settings  # noqa: E402
from policy_assistant.indexer import index_directory  # noqa: E402
from policy_assistant.vectorstore import PolicyVectorStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=3, help="top-k chunks to retrieve")
    parser.add_argument("--questions", type=Path, default=ROOT / "data" / "eval_questions.json")
    args = parser.parse_args()

    settings = Settings.from_env()
    questions = json.loads(args.questions.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmp:  # isolated store: never touches your real index
        store = PolicyVectorStore(tmp, "eval")
        index_directory(store, settings.sample_dir, settings)

        source_hits = answer_hits = 0
        reciprocal_ranks = []
        for item in questions:
            hits = store.query(item["question"], k=args.k)
            files = [h.file for h in hits]
            source_ok = item["expected_source"] in files
            answer_ok = any(item["expected_keyword"].lower() in h.text.lower() for h in hits)
            rank = files.index(item["expected_source"]) + 1 if source_ok else None
            source_hits += source_ok
            answer_hits += answer_ok
            reciprocal_ranks.append(1 / rank if rank else 0.0)
            mark = "PASS" if source_ok and answer_ok else "FAIL"
            print(f"[{mark}] {item['question']}  (top: {files[0] if files else '-'})")

    n = len(questions)
    print("\n--- Retrieval results ---")
    print(f"Questions        : {n}")
    print(f"Source hit@{args.k}     : {source_hits / n:.1%}")
    print(f"Answer hit@{args.k}     : {answer_hits / n:.1%}")
    print(f"MRR              : {sum(reciprocal_ranks) / n:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
