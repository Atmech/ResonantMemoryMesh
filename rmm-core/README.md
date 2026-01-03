# Resonant Memory Mesh (RMM) - The Infrastructure Layer for Living Memory

RMM is a high-performance, Rust-accelerated associative memory kernel designed for the next generation of AI agents. It moves beyond standard Vector Search (RAG) by implementing **Topological Resonance**, allowing information to be retrieved via causal chains and associative links.

> [!IMPORTANT]
> **Performance Benchmark**: Hot Query Latency: **1.1ms** | Throughput: **~900 queries/sec**.

## 🚀 Why RMM?

Standard RAG is limited by semantic similarity. RMM builds a **Reasoning Moat**:
- **Causal Retrieval**: Retrieve information 5+ hops away even with zero semantic similarity.
- **Atomic Pulse**: "Read-Your-Own-Writes" consistency for high-frequency agent updates.
- **Rust Kernel**: GIL-free parallelized BFS (v2.1 production baseline).
- **V-LRU Eviction**: Value-based Least Recently Used cache management to prevent RAM bloat.

## 🛠 Installation

```bash
# Build the Rust Kernel (Prerequisite)
cd rmm-rust && maturin develop --release

# Install the Python SDK
pip install rmm-core
```

## 📖 Quick Start

```python
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage

# Initialize with V5.1 "Reasoning" configuration
config = MeshConfig(beta=0.7, lambda_decay=0.1)
mesh = Mesh(InMemoryStorage(), config)

# Ingest and Link
id1 = mesh.ingest(vector1, metadata={"label": "Entry Point"})
id2 = mesh.ingest(vector2, metadata={"label": "Target"})
mesh.connect(id1, id2, weight=0.9)

# Query (Hot Query: < 1.1ms)
result = mesh.query(query_vector)
print(result.nodes[0].metadata['label'])
```

## 🔋 Infrastructure Support
RMM supports pluggable backends:
- **Memory**: High-speed prototyping.
- **Postgres + pgvector**: Production-grade persistent mesh.

See [GETTING_STARTED.md](../GETTING_STARTED.md) for the full "Causal Chain" walkthrough.
