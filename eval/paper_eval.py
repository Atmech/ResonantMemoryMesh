"""Single-query, fixed-depth MuSiQue experiment for Resonance Is All You Need."""
import argparse
import hashlib
import json
import logging
import random
import uuid
from importlib.metadata import version
from pathlib import Path
from unittest.mock import patch

import networkx as nx
import numpy as np
import torch
from datasets import Dataset, load_dataset
from sentence_transformers import SentenceTransformer

import run_eval as base


def balanced_followup(dataset):
    """Sample 100 eligible cases per hop count outside the original validation prefix."""
    groups = {2: [], 3: [], 4: []}
    for i in range(300, len(dataset)):
        example = dataset[i]
        hops = int(example["id"].split("hop", 1)[0])
        if hops in groups and any(p["is_supporting"] for p in example["paragraphs"]):
            groups[hops].append(i)
    rng = random.Random(20261119)
    indices = [i for group in groups.values() for i in rng.sample(group, 100)]
    return dataset.select(indices)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arrow", help="Optional local copy of the MuSiQue validation Arrow file")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sample", choices=["prefix", "balanced"], default="prefix")
    args = parser.parse_args()
    torch.set_num_threads(1)
    logging.disable(logging.WARNING)
    dataset = (Dataset.from_file(args.arrow) if args.arrow else
               load_dataset("dgslibisey/MuSiQue", revision="c8f4f8c9465fb69d31a8eae894c3fd509c4ca321",
                            split="validation"))
    if args.sample == "balanced":
        dataset = balanced_followup(dataset)
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu",
                                revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41")
    rows = []
    for example in dataset:
        paras = [p["paragraph_text"] for p in example["paragraphs"]]
        gold = [i for i, p in enumerate(example["paragraphs"]) if p["is_supporting"]]
        if not gold:
            continue
        vectors = base.embed_texts(model, [example["question"], *paras])
        q, docs = vectors[0], vectors[1:]
        similarities = docs @ q
        edges = base.build_cooccurrence_edges(base.extract_entities(paras))
        graph = nx.Graph()
        graph.add_nodes_from(range(len(paras)))
        graph.add_weighted_edges_from(edges)
        positive = np.maximum(similarities, 0)
        prior = dict(enumerate(positive.tolist())) if positive.sum() else None
        pr = nx.pagerank(graph, alpha=0.85, personalization=prior, weight="weight", max_iter=200)
        rankings = {"cosine": base.retrieve_vector_rag(q, docs, 5),
                    "pagerank": sorted(pr, key=pr.get, reverse=True)[:5]}
        ties = {}
        for key, build, extra in [
            ("proximity", base.build_rmm_proximity, [0.6]),
            ("entity", base.build_rmm_extracted, [edges]),
            ("oracle", base.build_rmm_oracle, [gold, q]),
        ]:
            # Identical paragraph IDs across graph conditions, independent of relevance labels.
            rng = random.Random(str(example["id"]))
            with patch.object(uuid, "uuid4", side_effect=lambda: uuid.UUID(int=rng.getrandbits(128), version=4)):
                mesh, lookup, _ = build(docs, paras, *extra)
            try:
                ranked = mesh.query(q, top_n=5).nodes
                rankings[key] = [lookup[node.id] for node in ranked[:5]]
                if key == "entity":
                    # Keep the exact same activated nodes and scores. Only split exact energy ties.
                    by_similarity = sorted(ranked, key=lambda node: (
                        -node.energy, -float(similarities[lookup[node.id]]), lookup[node.id]))
                    rankings["entity_cosine_ties"] = [lookup[node.id] for node in by_similarity[:5]]
                ties[key] = len(ranked) > 5 and ranked[4].energy == ranked[5].energy
            finally:
                mesh.close()
        rows.append({"id": example["id"], "gold": gold, "entity_edges": len(edges),
                     "rankings": {k: list(map(int, v)) for k, v in rankings.items()},
                     "cutoff_ties": ties,
                     "metrics": {k: base.compute_metrics(v, gold, example["answer"], paras)
                                 for k, v in rankings.items()}})
        if len(rows) % 50 == 0:
            print(f"{len(rows)} questions evaluated", flush=True)
        if len(rows) == 300:
            break
    assert len(rows) == 300
    keys = list(rows[0]["metrics"])
    scores = {k: np.array([r["metrics"][k]["supporting_recall"] for r in rows]) for k in keys}
    samples = np.random.default_rng(20261119).integers(len(rows), size=(10000, len(rows)))
    intervals = {}
    for a, b in [("proximity", "cosine"), ("entity", "pagerank"), ("entity_cosine_ties", "entity"),
                 ("entity_cosine_ties", "cosine")]:
        differences = scores[a] - scores[b]
        intervals[f"{a} minus {b}"] = [differences.mean(), *np.quantile(
            differences[samples].mean(axis=1), [0.025, 0.975])]
    report = {"sample": args.sample, "k": 5, "n": len(rows), "versions": {p: version(p) for p in
              ["numpy", "networkx", "torch", "datasets", "sentence-transformers", "spacy", "en-core-web-sm", "rmm-rust"]},
              "input_sha256": hashlib.sha256(Path(args.arrow).read_bytes()).hexdigest() if args.arrow else None,
              "means": {k: {m: np.mean([r["metrics"][k][m] for r in rows])
                            for m in rows[0]["metrics"][k]} for k in keys},
              "paired_intervals": intervals, "rows": rows}
    args.out.write_text(json.dumps(report, separators=(",", ":")) + "\n")
    print(json.dumps({k: report[k] for k in ("means", "paired_intervals")}, indent=2))


if __name__ == "__main__":
    main()
