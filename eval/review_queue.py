"""Replay an optional related-paragraph list against an equal-size cosine list."""
import argparse
import json
from pathlib import Path

import numpy as np
import torch
from datasets import Dataset, load_dataset
from sentence_transformers import SentenceTransformer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arrow", help="Local validation Arrow file (optional)")
    parser.add_argument("--results", default="eval/paper_balanced.json", type=Path)
    args = parser.parse_args()
    rows = json.loads(args.results.read_text())["rows"]
    data = Dataset.from_file(args.arrow) if args.arrow else load_dataset(
        "dgslibisey/MuSiQue", revision="c8f4f8c9465fb69d31a8eae894c3fd509c4ca321", split="validation")
    selected = {row["id"] for row in rows}
    by_id = {ex["id"]: ex for ex in data if ex["id"] in selected}
    torch.set_num_threads(1)
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu",
                                revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41")
    extra = 0
    gained = {"graph": 0, "cosine": 0}
    complete = {"graph": 0, "cosine": 0}
    for row in rows:
        example = by_id[row["id"]]
        texts = [example["question"], *[p["paragraph_text"] for p in example["paragraphs"]]]
        vec = model.encode(texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
        ranking = np.argsort(vec[1:] @ vec[0])[::-1].tolist()
        seeds = set(row["rankings"]["cosine"])
        assert set(ranking[:5]) == seeds
        union = seeds | set(row["rankings"]["entity"])
        gold = set(row["gold"])
        extra += len(union - seeds)
        for name, pool in [("graph", union), ("cosine", set(ranking[:len(union)]))]:
            gained[name] += len((pool - seeds) & gold)
            complete[name] += gold <= pool
    print(json.dumps(dict(questions=len(rows), extra=extra, gained=gained, complete=complete)))


if __name__ == "__main__":
    main()
