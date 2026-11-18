# RMM Multi-hop Retrieval Eval

A deterministic, LLM-free harness that tests whether Resonant Memory Mesh's
graph-propagation physics retrieve multi-hop supporting evidence better than
vanilla vector-RAG.

## What it measures

The engine's core claim is that it retrieves multi-hop evidence that vector
similarity alone misses. We test that claim directly on supporting-paragraph
recall — no answer generation, no LLM judge.

For each question we build a **fresh per-question corpus** from the question's
candidate paragraphs (exactly the distractor setting used in the dataset).
Three retrieval systems compete:

| System | Graph | Description |
|--------|-------|-------------|
| **vector-RAG** | none | Pure cosine similarity top-k. Baseline. |
| **RMM-proximity** | AutoLinker | RMM as shipped: edges built by cosine-threshold proximity on the candidate paragraphs. |
| **RMM-oracle-graph** | Gold chain | RMM with edges hand-wired along the gold supporting-fact chain + query-entry connection. Upper bound on "what the physics can do given a perfect graph." |

## Metrics (no LLM)

- **SupportingRecall@k** — fraction of gold supporting paragraphs that appear in the top-k retrieved set, averaged over questions. This is THE number.
- **AllFound@k** — fraction of questions where ALL gold supporting paragraphs appear in top-k (strict multi-hop success).
- **AnsRecall@k** — fraction of questions where the gold answer string appears verbatim (case-insensitive substring) in any top-k paragraph.

## Dataset

Downloaded at runtime (Hugging Face `datasets` library). Preference order:

1. MuSiQue-Answerable (`dgslibisey/MuSiQue` dev/validation)
2. HotpotQA distractor (`hotpot_qa`, validation)
3. 2WikiMultihopQA (`voidful/2wikimultihopqa`, validation)

First 300 questions are used (configurable via `--n`).

## How to run

```bash
# Default: N=300, k=2,5,10
.venv/bin/python eval/run_eval.py

# Custom
.venv/bin/python eval/run_eval.py --n 100 --k 2 5 10 --threshold 0.6

# Specific dataset
.venv/bin/python eval/run_eval.py --dataset hotpot --n 300
```

Output:
- Prints a markdown table to stdout
- Saves raw per-metric summary to `eval/results.json`

## Honesty caveats

1. **Per-question corpus**: each question provides its own distractor paragraphs (typically 10–20). All systems index the same set. This advantages all systems equally vs. a real open-corpus retrieval scenario, but is the standard evaluation protocol for these datasets.

2. **RMM-proximity graph quality**: AutoLinker connects paragraphs whose cosine similarity exceeds a threshold (default 0.6). In a distractor setting with diverse paragraphs, few proximity edges may form. This is reported honestly — if RMM-proximity matches or loses to vector-RAG, that is the real result.

3. **RMM-oracle-graph** is an upper bound only. It uses gold labels that are not available at inference time. It answers: "given a perfect graph, does the energy-propagation physics help?" It does NOT represent a deployable system.

4. **No ignition events**: logged when `mesh.query()` returns zero nodes. These contribute 0 to all metrics (penalizing RMM fairly).

5. **Embedding model**: `all-MiniLM-L6-v2` (local, 384-dim). No external API calls.

6. **Threshold was NOT tuned to favor RMM**. The default 0.6 is the RMM default in `MeshConfig`. To experiment with other values, use `--threshold`.
