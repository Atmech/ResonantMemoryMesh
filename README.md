# Resonant Memory Mesh (RMM)

**A topology-aware associative memory kernel for AI agents.**

> Memory as a physical system — not a database.

RMM models memory as a dissipative dynamical system where retrieval emerges from energy propagation through topological structure. It enables retrieval across multi-hop causal chains where traditional RAG fails — bridging semantic discontinuities that vector similarity cannot cross.

---

## Why RMM?

Standard RAG retrieves by semantic similarity. When causal chains span concepts with **zero semantic overlap**, RAG fails categorically — the target never enters the candidate set.

RMM solves this with **topological resonance**: energy propagates through weighted edges, activating causally linked memories regardless of embedding distance.

| | Standard RAG | RMM |
|---|---|---|
| Retrieval | Cosine similarity (semantic) | Energy propagation (topological) |
| Multi-hop causal chains | ❌ Fails at semantic gaps | ✅ Traverses 5+ hops |
| Hot query latency | — | **~2ms median** (warm, in-memory, 1000 nodes, single core — measured; see `benchmarks/latency.py`) |
| Throughput | — | **~490 sequential qps** (single-threaded, in-memory, 1000 nodes — measured; concurrent throughput not yet benchmarked) |

---

## Installation

```bash
# Install the Python SDK
pip install rmm-core

# Build the Rust kernel (optional, for production performance)
cd rmm-rust && maturin develop --release
```

**Requirements:** Python ≥ 3.10, NumPy ≥ 1.24. Rust kernel requires [Rust](https://rustup.rs/) and [maturin](https://github.com/PyO3/maturin).

---

## Quickstart

```python
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage

config = MeshConfig(beta=0.7, lambda_decay=0.1)
mesh = Mesh(InMemoryStorage(), config)

id1 = mesh.ingest(vector1, metadata={"label": "Entry Point"})
id2 = mesh.ingest(vector2, metadata={"label": "Target"})
mesh.connect(id1, id2, weight=0.9)

result = mesh.query(query_vector, top_n=5)
print(result.nodes[0].metadata["label"])
```

See [`examples/quickstart.py`](examples/quickstart.py) for a complete runnable demo.

---

## The Bob/Alice Benchmark

The core demonstration: retrieve across a 5-hop causal chain with **zero semantic signal** between entry and target (cosine similarity = 0.28).

```python
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage

mesh = Mesh(InMemoryStorage(), MeshConfig(beta=0.7, lambda_decay=0.1))

# Build a 5-hop causal chain
facts = [
    "Bob was recently hired as Managing Director at Mars Capital.",
    "Mars Capital led the Series A for Alice's startup, TechCorp.",
    "TechCorp's product relies on hardware from Quantum Silicon.",
    "Quantum Silicon was acquired by Apex Holdings.",
    "Apex Holdings has an exclusive contract with Omega Inc.",
]
ids = [mesh.ingest(embed(f), metadata={"fact": f}) for f in facts]
for i in range(len(ids) - 1):
    mesh.connect(ids[i], ids[i + 1], weight=0.9)

# Query: "Does Bob have any connection to Omega Inc.?"
result = mesh.query(embed("Bob connection to Omega Inc"), top_n=10)
# → Target node (Omega) retrieved at rank 9 via resonance
# → RAG returns nothing (cosine 0.28 < retrieval threshold)
```

```
Energy propagation: 3.09 → 1.87 → 0.94 → 0.31 → 0.077
                    Node1   Node2   Node3   Node4   Node5
                   (Bob)                           (Omega)

RAG similarity:     0.28 ────────────────────────── 0.28  (flat, no signal)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Python SDK (rmm-core)                   │
│             Mesh.query() / ingest() / connect()          │
└─────────────────────────┬───────────────────────────────┘
                          │ Zero-Copy FFI
┌─────────────────────────▼───────────────────────────────┐
│                  Rust Kernel (rmm-rust)                   │
│  Parallel BFS (Rayon) → DashMap L1 Cache (lock-free)     │
│  AtomicPing propagation → Hub dampening → V-LRU eviction │
└─────────────────────────┬───────────────────────────────┘
                          │ Async Write-Back
┌─────────────────────────▼───────────────────────────────┐
│              L2 Store (PostgreSQL + pgvector)             │
│         Persistent graph · Embeddings · Metadata          │
└─────────────────────────────────────────────────────────┘
```

**Key components:**
- **[rmm-core/](rmm-core/)** — Python SDK: Mesh API, adapters (in-memory, Postgres), AutoLinker, adaptive tuning
- **[rmm-rust/](rmm-rust/)** — Rust kernel: parallel BFS, DashMap L1 cache, PyO3 bindings

---

## Configuration

RMM's physics engine is controlled by a small set of parameters passed via `MeshConfig`:

| Parameter | Default | Description |
|---|---|---|
| `beta` | 0.5 | **Dissipative Gain** — energy transfer ratio per hop. Higher = more energy propagates. |
| `lambda_decay` | 0.1 | **Decay rate** — how fast idle nodes lose energy over time. |
| `max_hops` | 5 | **BFS depth** — maximum causal chain length to traverse. |
| `e_max` | 10.0 | **Heat Death limit** — energy ceiling to prevent runaway amplification. |
| `epsilon` | 0.01 | **Pruning threshold** — nodes below this energy are excluded from results. |
| `max_neighbors` | 50 | **Fan-out cap** — max neighbors processed per node per hop. |
| `min_weight` | 0.05 | **Edge filter** — edges below this weight are ignored during traversal. |
| `hub_threshold` | 100 | **Hub detection** — degree above which hub dampening activates. |
| `hub_dampening_alpha` | 0.5 | **Hub penalty** — dampening strength for high-degree nodes. |

### Tuning Guide

- **Shallow graphs (2–3 hops):** Increase `beta` (0.7–0.9), reduce `max_hops` to 3.
- **Deep causal chains (5+ hops):** Lower `beta` (0.3–0.5) so energy survives the full chain.
- **High-churn data:** Increase `lambda_decay` (0.3+) to forget stale nodes faster.
- **Hub-heavy graphs:** Lower `hub_threshold` and raise `hub_dampening_alpha` to prevent hubs from dominating results.
- **Precision over recall:** Raise `epsilon` and `min_weight` to tighten the result set.

Parameters can be overridden at runtime via environment variables prefixed with `RMM_` (e.g., `RMM_MAX_HOPS=3`).

---

## Project Structure

```
rmm/
├── README.md
├── LICENSE              # Apache 2.0
├── rmm-core/            # Python SDK
│   ├── pyproject.toml
│   ├── rmm/
│   └── tests/
├── rmm-rust/            # Rust kernel
│   ├── Cargo.toml
│   └── src/
├── examples/
│   └── quickstart.py
```

---

## Contributing

Contributions welcome. Please open an issue first to discuss proposed changes.

## License

[Apache License 2.0](LICENSE) — Copyright 2025 Affan Tanke
