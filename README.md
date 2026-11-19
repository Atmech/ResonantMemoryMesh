# Resonant Memory Mesh

Research code for **Resonance Is All You Need** by Affan Tanke. The study asks whether a graph can retrieve a supporting paragraph that a question’s closest embedding matches miss. [Paper on Zenodo](https://doi.org/10.5281/zenodo.24355596) · [PDF](rmm_paper.pdf) · [LaTeX source](rmm_paper.tex)

RMM starts with passages selected by cosine similarity, sends activation along weighted links, and ranks the passages it reaches. Under the paper’s initialization and clipping rule, a newly reached passage can only tie a starting passage. With five starting passages and five places in the result, tie-breaking can decide which evidence a reader sees.

## Results

Mean supporting-paragraph recall among the top five retrieved passages on two disjoint MuSiQue validation samples:

| Retrieval method | 300 two-hop questions | 300 questions balanced across 2–4 hops |
| --- | ---: | ---: |
| Cosine search | 66.5% | 57.9% |
| RMM with proximity links | 64.5% | 56.1% |
| RMM with shared-entity links | 43.7% | 41.3% |
| Personalized PageRank on the same entity graph | 60.2% | 51.7% |

Breaking equal RMM activation scores by query similarity recovered the original five cosine matches on all 600 questions. In an exploratory follow-up, keeping those matches and adding graph suggestions gave complete supporting evidence for **103 of 300** questions. Extending cosine search to the same list length on each question did so for **92 of 300**. This comparison used supplied passage pools and measured evidence coverage before answer generation.

## Reproduce the paper tables

From the repository root, run the following with Python 3. It reads the saved rankings and uses only the standard library.

```sh
python3 eval/check_tables.py
```

The evaluation guide includes the question-level outputs, dependencies, and commands to rerun retrieval and the supplementary-passage comparison. [Evaluation guide](eval/README.md)

## Try the mesh

The Python SDK calls a compiled Rust extension. From the repository root, with Python 3.13 and a Rust toolchain installed:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 python -m pip install ./rmm-rust ./rmm-core
python examples/quickstart.py
```

The example uses three fixed vectors and explicit links so the traversal is easy to inspect. The paper evaluates automatically constructed links separately. [Python interface](rmm-core/README.md) · [Rust kernel](rmm-rust/README.md)

## Citation and license

Affan Tanke (2026). *Resonance Is All You Need*. Zenodo. [Version DOI](https://doi.org/10.5281/zenodo.24355596)

The repository code is available under the [Apache License 2.0](LICENSE).
