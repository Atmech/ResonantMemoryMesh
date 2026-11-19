"""Print both paper tables and the diagnostic counts from the recorded rankings."""
import json
from pathlib import Path
from statistics import mean

root = Path(__file__).resolve().parent
runs = [json.loads((root / name).read_text())["rows"]
        for name in ("paper_top5.json", "paper_balanced.json")]
identifiers = [{row["id"] for row in rows} for rows in runs]
assert all(len(ids) == 300 for ids in identifiers)
assert identifiers[0].isdisjoint(identifiers[1])


def metrics(row, method):
    gold = set(row["gold"])
    ranked = set(row["rankings"][method])
    assert len(ranked) == 5
    recall = len(gold & ranked) / len(gold)
    complete = int(gold <= ranked)
    assert recall == row["metrics"][method]["supporting_recall"]
    assert complete == row["metrics"][method]["all_found"]
    return recall, complete, row["metrics"][method]["answer_recall"]


def same_seeds(row):
    return set(row["rankings"]["cosine"]) == set(row["rankings"]["entity_cosine_ties"])


print("Table 1. Discovery and follow-up: support recall, complete support, answer hit (%)")
for key in ("cosine", "proximity", "entity", "pagerank", "entity_cosine_ties", "oracle"):
    cells = [f"{100 * mean(column):.1f}" for rows in runs
             for column in zip(*(metrics(row, key) for row in rows))]
    print(key, *cells)
print("Table 2. Follow-up: cosine, entity RMM, PageRank (%), exact set matches")
for hops in (2, 3, 4):
    group = [r for r in runs[1] if int(r["id"].split("hop", 1)[0]) == hops]
    assert len(group) == 100
    print(hops, *(f"{100 * mean(metrics(r, key)[0] for r in group):.1f}"
                  for key in ("cosine", "entity", "pagerank")), sum(map(same_seeds, group)))
for rows in runs:
    gained = lost = 0
    for r in rows:
        gold = set(r["gold"])
        seeds = set(r["rankings"]["cosine"])
        result = set(r["rankings"]["entity"])
        gained += len(gold & (result - seeds))
        lost += len(gold & (seeds - result))
    print("Cutoff ties, exact matches, gained, lost:",
          sum(r["cutoff_ties"]["entity"] for r in rows), sum(map(same_seeds, rows)), gained, lost)
