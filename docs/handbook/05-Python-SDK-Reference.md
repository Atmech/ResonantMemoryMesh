# Python SDK Reference

The RMM Python SDK (`rmm-core`) provides the primary interface for managing and querying your Living Memory. 

This reference covers the core classes and their methods.

## The `Mesh` Class

The `Mesh` class is your main entry point for interacting with the graph.

```python
from rmm import Mesh, MeshConfig
```

### Initialization

```python
mesh = Mesh(storage, config)
```
- `storage`: An instance of a storage backend (e.g., `InMemoryStorage` or `PostgresStorage`).
- `config`: A `MeshConfig` object configuring the resonance dynamics.

### `Mesh.ingest()`

Ingests a new node into the mesh.

```python
node_uuid = mesh.ingest(vector, metadata=None, significance=1.0)
```
- **Returns:** The generated `UUID` for the new node.
- **`vector` (np.ndarray):** A dense 1D `numpy` vector containing the embedding. Must be `float32`.
- **`metadata` (Optional[dict]):** Standard python dictionary storing data like text strings, labels, and timestamps.
- **`significance` (float):** The base importance of the node. Default is 1.0. High-significance nodes cast a wider resonance net.

### `Mesh.connect()`

Creates a directed edge between two nodes.

```python
mesh.connect(source_val, target_val, weight=1.0)
```
- **`source_val` (UUID):** The starting node.
- **`target_val` (UUID):** The receiving node.
- **`weight` (float):** The conductivity of the edge. Value between 0.0 and 1.0. A weight of 1.0 ensures maximum energy transfer during a resonance query.

### `Mesh.flush()`

Synchronizes the Python SDK's in-memory edge cache with the chosen persistent `storage` backend.
**Critical:** You must call `flush()` after calling `connect()`, otherwise your edges may not be traversed during a query!

```python
mesh.flush()
```

### `Mesh.query()`

Executes a topological resonance search.

```python
result = mesh.query(query_vector, top_n=5)
```
- **Returns:** A `ResonanceResult` object containing `.nodes` (list of activated nodes) and their accumulated `.energy`.
- **`query_vector` (np.ndarray):** The vector to inject energy into the mesh.
- **`top_n` (int):** The maximum number of nodes to return in the result set.

### `Mesh.close()`

Closes the active storage connection and safely terminates the mesh instance.

```python
mesh.close()
```

---

## Mesh Configuration (`MeshConfig`)

The `MeshConfig` object fine-tunes the physical parameters of the Rust Kernel.

```python
config = MeshConfig(
    beta=0.7, 
    lambda_decay=0.5
)
```
- **`beta` (Gain):** Controls how much energy flows across edges. High `beta` values allow energy to flow further through the causal chain. Low `beta` restricts energy to immediate neighbors.
- **`lambda_decay`:** Controls the baseline decay of energy on the graph. A high decay means energy drops off sharply, limiting the "depth" of the reasoning moat.

---

## Storage Adapters

### `InMemoryStorage`

Best for testing, Jupyter notebooks, or short-lived applications.

```python
from rmm.adapters.memory import InMemoryStorage
storage = InMemoryStorage()
```

### `PostgresStorage` (Upcoming)

Required for production environments. Connects to a standard PostgreSQL database, leveraging `pgvector` for initial similarities and standard relational tables for graph traversal.

```python
from rmm.adapters.pg import PostgresStorage
storage = PostgresStorage(dsn="postgresql://user:pass@localhost:5432/rmm_db")
```
