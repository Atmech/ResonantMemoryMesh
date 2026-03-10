# Upcoming Features

Resonant Memory Mesh is rapidly evolving. The `0.1.x` architecture proves the validity of the "Reasoning Moat." The upcoming milestones are focused purely on **scale, distributed persistence, and analytics**. 

Here is what is currently in development for RMM.

## 1. The Postgres Storage Adapter (Production Readiness)

Currently, the `InMemoryStorage` adapter is excellent for conceptual testing and lightweight agentic loops. However, biological memory is persistent, and so too must be RMM.

The upcoming `PostgresStorage` adapter fundamentally shifts RMM from a sandbox tool to a production-grade infrastructure layer.

### Nuances and Quirks
- **`pgvector` Integration:** The Postgres adapter will rely heavily on the `pgvector` extension. Initial node activation (finding the entry point before graph traversal) will be optimized using HNSW indexes on the `vector` column.
- **Relational Graph Storage:** Edges will be stored in standard relational tables. This allows for complex joins and transactional guarantees when updating memory states.
- **Hybrid Traversal:** The most significant challenge in development is seamlessly moving the initial `pgvector` activation results out of the PostgreSQL database and feeding them into the Rust kernel for high-speed, in-memory resonance, and then flushing state changes back down.

## 2. Dynamic Graph Scaling and Pruning

Human memory is not append-only; it prunes unused connections.

- **Synaptic Pruning:** Future versions of RMM will introduce a background garbage-collection process. Edges that are never traversed during queries, or nodes whose `significance` decays below a certain threshold over time, will be automatically severed to optimize graph density.
- **Auto-Weighting (Synaptic Plasticity):** Conversely, edges that frequently transmit energy during successful queries will have their `weight` dynamically increased. The mesh will literally *learn* which reasoning paths are correct.

## 3. Advanced Topology Metrics

Understanding *why* the mesh returned a specific result is critical for debugging agent behavior.

- **Centrality Clustering:** New APIs will expose metrics on "memory gravity"—identifying which nodes are acting as massive hubs of information within the network.
- **Path Tracing:** The `ResonanceResult` object will be updated to include not just the activated nodes, but the specific **Causal Path** (the list of edges) that the energy traveled to reach the destination node. This provides total explainability for the LLM.

## 4. Distributed RMM (Multi-Node Clusters)

For terabyte-scale meshes (e.g., ingesting an entire corporate intranet and establishing reasoning edges between every document), the graph will need to be partitioned. Support for sharded mesh topologies, allowing the resonance pulse to travel across network boundaries via gRPC, is slated for future development.
