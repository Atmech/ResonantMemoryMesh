# Quickstart

This guide provides a basic walk-through to get your first Resonant Memory Mesh up and running. We will cover initializing a mesh, ingesting data, building edges, and executing your first topological query.

## 1. Initialization

Start by importing the necessary components from `rmm-core`. You must provide a **Storage** backend and a **Config** object.

```python
import numpy as np
import uuid
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage

# 1. Setup the storage adapter
storage = InMemoryStorage()

# 2. Configure mesh dynamics (beta controls energy propagation gain)
config = MeshConfig(beta=0.7, lambda_decay=0.5)

# 3. Initialize the Mesh
mesh = Mesh(storage, config)
```

## 2. Ingesting Nodes

RMM nodes require a dense vector (an embedding). You can generate these using any embedding model (e.g., OpenAI's `text-embedding-3-small`, HuggingFace's `all-MiniLM-L6-v2`).

For this example, we will generate fake embeddings for a mini investigation scenario. Let's say we are tracking stolen funds.

```python
# Helper to simulate an embedding model
def get_embedding(text: str) -> np.ndarray:
    return np.random.randn(128).astype(np.float32)

# Concept 1: The initial crime
event_1 = "The Alpha Bank vault was breached at midnight."
id_alpha = mesh.ingest(get_embedding(event_1), metadata={"text": event_1, "type": "crime"}, significance=1.0)

# Concept 2: The getaway vehicle
event_2 = "A black van license plate XYZ-123 was seen fleeing Alpha Bank."
id_van = mesh.ingest(get_embedding(event_2), metadata={"text": event_2, "type": "vehicle"}, significance=0.8)

# Concept 3: The suspect
event_3 = "John Doe recently registered a black van with plate XYZ-123."
id_suspect = mesh.ingest(get_embedding(event_3), metadata={"text": event_3, "type": "suspect"}, significance=0.9)

print(f"Ingested nodes successfully!")
```

## 3. Connecting the Nodes

We've added isolated nodes. To unlock RMM's power, we must link them. Let's create an investigative chain: `The Crime -> The Van -> The Suspect`.

```python
# Connect the crime to the van spotted at the scene
mesh.connect(id_alpha, id_van, weight=0.85)

# Connect the van to its registered owner
mesh.connect(id_van, id_suspect, weight=0.90)

# IMPORTANT: Always flush to persist edges to storage!
mesh.flush()
```

By connecting these discrete entities, we've constructed a reasoning path that the kernel can traverse. We are explicitly teaching the RMM the causality of our data.

## 4. Querying

Let's query the mesh. We will ask a question that is highly similar to the first node ("The Alpha Bank vault was breached").

```python
query_text = "Who breached the Alpha Bank?"
query_vector = get_embedding(query_text)

# Query the mesh, requesting the top 3 most resonant nodes
results = mesh.query(query_vector, top_n=3)

print("--- Query Results ---")
for node in results.nodes:
    print(f"Energy: {node.energy:.4f} | Data: {node.metadata.get('text')}")
```

### The Magic of Resonance

Even if the embedding for John Doe registering a van is mathematically orthogonal (completely dissimilar) to the question *"Who breached the Alpha Bank?"*, **John Doe will appear in your result set.**

Because the query vector closely matched the Alpha event, energy flowed from the Bank Breach, through the Black Van, directly into John Doe. The resulting energy profile reflects the logical topology, bypassing the limitations of flat semantic searches. You have built a memory that can reason!

## 5. Teardown

Always close your connection when finished to ensure resources are cleanly released.

```python
mesh.close()
```
