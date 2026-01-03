# Getting Started with RMM

Resonant Memory Mesh (RMM) is an infrastructure layer for "Living Memory." It allows AI systems to retrieve information not just by semantic similarity, but by **topological resonance**.

This guide follows the **Causal Chain** pattern, proving how RMM can find deeply linked information that standard RAG misses.

## 1. Installation

First, ensure you have the Rust kernel built, then install the Python SDK:

```bash
# Build the Rust Kernel
cd rmm-rust
maturin develop --release

# Install RMM Core
cd ../rmm-core
pip install .
```

## 2. Ingesting Data

RMM nodes represent concepts or memory chunks. Each node has a vector (embedding) and an optional label.

```python
import numpy as np
import uuid
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage

# 1. Setup
storage = InMemoryStorage()
mesh = Mesh(storage, MeshConfig(beta=0.7))

# 2. Ingest the "Causal Chain"
# Node 1 is our entry point (e.g., "Officer Chen")
v1 = np.random.randn(128).astype(np.float32)
id1 = mesh.ingest(v1, metadata={"label": "Officer Chen"}, significance=1.0)

# Node 5 is our target ("Mars Capital"), 4 hops away
# It is semantically UNRELATED to the query vector
v5 = np.random.randn(128).astype(np.float32)
id5 = mesh.ingest(v5, metadata={"label": "Mars Capital"}, significance=1.0)

# Ingest filler nodes for the chain
ids = [id1, mesh.ingest(np.random.randn(128)...), ..., id5]
```

## 3. Connecting the Mesh

Edges allow energy to flow between nodes. This is the "Reasoning Moat."

```python
# Connect Node 1 to Node 5 through a chain
# 1 -> 2 -> 3 -> 4 -> 5
mesh.connect(id1, id2, weight=0.9)
mesh.connect(id2, id3, weight=0.9)
mesh.connect(id3, id4, weight=0.9)
mesh.connect(id4, id5, weight=0.9)

# Essential: Flush to ensure edges are persisted/cached
mesh.flush()
```

## 4. Performing a Resonance Query

When you query with a vector similar to **Node 1**, energy will flow through the chain and activate **Node 5**, even if Node 5's vector is orthogonal to the query.

```python
# Query with a vector similar to Node 1
query_vector = v1 + np.random.randn(128) * 0.01
results = mesh.query(query_vector, top_n=5)

for node in results.nodes:
    print(f"Ranked Node: {node.metadata['label']} | Energy: {node.energy:.4f}")
    
# Node 5 will appear in the results despite zero semantic similarity!
```

## 5. Cleaning Up

```python
mesh.close()
```

## Next Steps
- Use the **Postgres Adapter** for persistent, large-scale meshes.
- Tune `beta` (Gain) and `lambda_decay` to control the "depth" of your memory's reasoning.
