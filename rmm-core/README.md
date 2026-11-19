# RMM Python SDK

The `rmm` package exposes the ingestion, graph construction, and retrieval interface used in *Resonance Is All You Need*. Install it together with the Rust extension from the repository root. [Build instructions](../README.md#try-the-mesh)

- `Mesh.ingest(vector, metadata)` normalizes a vector, stores a node, and returns its ID. The proximity linker is configurable through `MeshConfig`.
- `Mesh.connect(source, target, weight)` adds a directed edge. Add the reverse edge explicitly when the relationship should be traversable both ways.
- `Mesh.query(query_vector, top_n=k)` selects up to `k` entry nodes and returns the activated nodes ordered by energy. Use `result.nodes[:k]` for a fixed-size result. The entry IDs are available in `result.entry_ids`.
- `Mesh.flush()` writes buffered nodes and links to storage. Using the mesh as a context manager closes its buffers on exit.

The paper uses the in-memory adapter. The optional PostgreSQL adapter uses pgvector and the schema in [sql/schema.sql](sql/schema.sql). [Runnable example](../examples/quickstart.py) · [Paper evaluation](../eval/README.md)
