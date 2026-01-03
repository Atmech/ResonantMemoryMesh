"""
RMM Mesh - High-level SDK entry point.

Primary interface for developers using Resonant Memory Mesh.
Handles kernel orchestration, buffered writes, and rationale synthesis.
"""
import time
import uuid
import logging
from typing import Optional, List, Tuple

import numpy as np

# Import the Rust Crate
try:
    import rmm_rust
except ImportError:
    logging.warning("rmm_rust module not found. Ensure it is built with maturin.")
    raise

from rmm import Node, Edge, MeshConfig, QueryResult
from rmm.adapters.base import BaseStorage
from rmm.core.buffer import WriteBackBuffer
from rmm.core.synthesizer import generate_structural_rationale

logger = logging.getLogger(__name__)

class Mesh:
    """
    Primary SDK interface for Resonant Memory Mesh.
    Delivers High-Performance via Rust Kernel + Zero-Copy Bridge.
    """
    
    def __init__(self, storage: BaseStorage, config: MeshConfig = None):
        self.config = config or MeshConfig()
        self.storage = storage
        
        # Initialize Rust Kernel
        # Bridge MeshConfig (Python) -> KernelConfig (Rust)
        rust_config = rmm_rust.KernelConfig()
        rust_config.beta = float(self.config.beta)
        rust_config.lambda_decay = float(self.config.lambda_decay)
        rust_config.max_hops = int(self.config.max_hops)
        rust_config.e_max = float(self.config.e_max)
        rust_config.epsilon = float(self.config.epsilon)
        
        self.cache = rmm_rust.L1Cache()
        self.kernel = rmm_rust.RustKernel(rust_config)
        
        # Node buffer with SyncThread hook for Rust L1 updates
        self.node_buffer = WriteBackBuffer(
            storage_write_fn=self._flush_nodes_to_storage,
            key_func=lambda n: n.id,
            num_shards=self.config.buffer_shards,
            flush_interval_ms=self.config.buffer_flush_ms,
        )
        
        # Edge buffer
        self.edge_buffer = WriteBackBuffer(
            storage_write_fn=self._flush_edges_to_storage,
            key_func=lambda e: (e.source, e.target),
            num_shards=self.config.buffer_shards,
            flush_interval_ms=self.config.buffer_flush_ms,
        )
        
        self._started = False
        
    def _flush_nodes_to_storage(self, nodes: List[Node]) -> None:
        """SyncThread Entry Point for Nodes."""
        # 1. Write to L2
        self.storage.upsert_nodes(nodes)
        # 2. Update Rust L1 (Zero-Copy)
        self._update_rust_l1(nodes)

    def _flush_edges_to_storage(self, edges: List[Edge]) -> None:
        """SyncThread Entry Point for Edges."""
        # 1. Write to L2
        self.storage.upsert_edges(edges)
        # 2. Update Rust L1
        self._update_rust_l1_edges(edges)

    def _update_rust_l1(self, nodes: List[Node]) -> None:
        """Helper to push nodes to Rust L1 using Zero-Copy raw bytes."""
        raw_data = []
        for n in nodes:
            # Extract label from metadata or use ID
            # In V5.1, we might use a dedicated field, but for now metadata['label']
            label = "Unknown"
            if n.metadata and 'label' in n.metadata:
                label = str(n.metadata['label'])
            
            # (uuid_bytes, label, vector, energy, last_update, significance)
            raw_data.append((
                n.id.bytes,
                label,
                n.vector,
                n.energy,
                n.last_update,
                n.significance
            ))
        
        # Invoke Rust directly
        self.cache.update_batch_raw(raw_data)

    def _update_rust_l1_edges(self, edges: List[Edge]) -> None:
        """Helper to push edges to Rust L1."""
        rust_edges = []
        for e in edges:
            if not isinstance(e, Edge): 
                continue
            # RustEdge constructor requires arguments
            re = rmm_rust.RustEdge(str(e.source), str(e.target), e.weight)
            rust_edges.append(re)
        
        self.cache.update_edges_batch(rust_edges)


    def start(self) -> None:
        """Start background flush threads."""
        if not self._started:
            self.node_buffer.start()
            self.edge_buffer.start()
            self._started = True
    
    def query(self, query_vector: np.ndarray, top_n: int = 5) -> QueryResult:
        """
        Execute resonance query with Fault-In (Cold Start) and Atomic Pulse.
        """
        # Ensure started
        if not self._started:
            self.start()
        
        # 1. Vector search → candidate IDs
        candidate_ids = self.storage.vector_search(query_vector, top_k=top_n * 3)
        
        if not candidate_ids:
            return QueryResult(nodes=[], rationale="No resonance detected.", entry_ids=[])
        
        # 2. Hybrid Ignition: re-rank by combined score
        alpha = self.config.hybrid_alpha
        query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-9)
        
        # Check L1 first for candidates (Optimization)
        # Identify which candidates are in L1 vs need L2 fetch
        l1_nodes = {}
        missing_in_l1 = []
        
        for nid in candidate_ids:
            # Try to get from Rust L1
            # Note: get_node_raw returns RustNode or None
            rn = self.cache.get_node_raw(nid.bytes)
            if rn:
                # Convert to Python Node for scoring
                # RECOVERY: Reconstruct Node from Rust L1
                # Note: RustNode now has .label
                meta = {'label': rn.label} if hasattr(rn, 'label') else {}
                
                l1_nodes[nid] = Node(
                    id=nid,
                    vector=np.array(rn.vector, dtype=np.float32),
                    energy=rn.energy,
                    last_update=rn.last_update,
                    significance=rn.significance,
                    metadata=meta
                )
            else:
                missing_in_l1.append(nid)
        
        if missing_in_l1:
            logger.warning(f"Hybrid Ignition: L1 Miss for {len(missing_in_l1)} nodes")
        
        # Fetch missing from Storage (L2)
        l2_nodes = {}
        if missing_in_l1:
            l2_nodes = self.storage.batch_get_nodes(missing_in_l1)
            # PASSIVE WARMING: Push fetched nodes to L1 so next query is Hot
            if l2_nodes:
                self._update_rust_l1(list(l2_nodes.values()))
            # PASSIVE WARMING: Push fetched nodes to L1 so next query is Hot
            if l2_nodes:
                self._update_rust_l1(list(l2_nodes.values()))
            
        candidate_nodes = {**l1_nodes, **l2_nodes}
        scored = []
        
        for nid in candidate_ids:
            node = candidate_nodes.get(nid)
            if not node:
                continue
            similarity = float(np.dot(query_norm, node.vector))
            hybrid_score = (similarity * alpha) + (node.significance * (1 - alpha))
            scored.append((nid, hybrid_score))
        
        # Sort by hybrid score descending
        scored.sort(key=lambda x: -x[1])
        entry_ids = [s[0] for s in scored[:top_n]]
        
        # 3. FAULT-IN: Ensure entries and neighbors are in L1 (Cold Start Support)
        # Check if neighbors are loaded (Edge Warmth). 
        # Passive Warming only loads Nodes. We need Edges for BFS.
        missing_ids = []
        for eid in entry_ids:
            # We assume if we have 0 neighbors in L1, we might need to fetch.
            # (Optimization: In a real system we'd track 'edge_loaded' flag)
            neighbors = self.cache.get_neighbors(str(eid))
            if not neighbors:
                logger.warning(f"Fault-In: Neighbors missing for {eid}")
                missing_ids.append(eid)
        
        if missing_ids:
            logger.warning(f"Fault-In: Fetching neighbors for {len(missing_ids)} nodes")
            # Sync missing nodes (if any logic required, but mostly for edges now)
            # Actually we already have nodes from Step 2 (Passive Warming)
            
            # Sync missing neighbors (Crucial for BFS)
            # Fetch neighbors for all missing IDs in one batch
            neighbors_map = self.storage.fetch_neighbors(missing_ids)
            
            all_neighbor_ids_to_fetch = set()
            count_entries_warmed = 0
            
            for mid in missing_ids:
                neighbors = neighbors_map.get(mid, [])
                if neighbors:
                    # 1. Sync ALL edges (Lightweight structure)
                    self._update_rust_l1_edges(neighbors)
                    count_entries_warmed += 1
                    
                    # 2. Identify Top-10 Nodes to Warm
                    # Sort by weight desc
                    neighbors.sort(key=lambda e: -e.weight)
                    top_neighbors = neighbors[:10]
                    
                    for e in top_neighbors:
                        all_neighbor_ids_to_fetch.add(e.target)
            
            # 3. Global Batch Fetch for Neighbor Bodies (1 Round-Trip)
            if all_neighbor_ids_to_fetch:
                neighbor_nodes_map = self.storage.batch_get_nodes(list(all_neighbor_ids_to_fetch))
                if neighbor_nodes_map:
                    self._update_rust_l1(list(neighbor_nodes_map.values()))
                    
            logger.warning(f"Fault-In: Processed {count_entries_warmed} entries, Warmed {len(all_neighbor_ids_to_fetch)} neighbor nodes (Global Batch)")

        # 4. Kernel propagation (Rust Hot Path)
        entry_bytes = [eid.bytes for eid in entry_ids]
        rust_nodes = self.kernel.execute_raw(entry_bytes, self.cache, None)
        
        # Convert RustNode back to Python Node objects
        activated_nodes = []
        ids_to_dirty = []
        for rn in rust_nodes:
            nid = uuid.UUID(rn.id)
            node = Node(
                id=nid,
                vector=np.array(rn.vector, dtype=np.float32),
                energy=rn.energy,
                last_update=rn.last_update,
                significance=rn.significance,
                metadata={'label': rn.label} if hasattr(rn, 'label') else {}
            )
            activated_nodes.append(node)
            ids_to_dirty.append(node)
            
        # Sort activated nodes by Energy (Descending) for deterministic output
        activated_nodes.sort(key=lambda n: -n.energy)

        # 5. Buffer updates (Async write-back of energy)
        for node in ids_to_dirty:
            self.node_buffer.mark_dirty(node)
            self._update_rust_l1([node])
        
        # 6. Synthesize
        # Pass self (Mesh) to synthesizer so it can use fetch_neighbors (L1 Cache aware)
        rationale = generate_structural_rationale(activated_nodes, self)
        
        return QueryResult(nodes=activated_nodes, rationale=rationale, entry_ids=entry_ids)
    
    def fetch_neighbors(self, node_ids: List[uuid.UUID]) -> dict:
        """
        L1 Cache Aware Fetch. Used by Synthesizer.
        """
        result = {}
        missing = []
        
        for nid in node_ids:
            # Check L1
            rust_edges = self.cache.get_neighbors(str(nid))
            if rust_edges:
                # Convert RustEdge -> Edge
                edges = []
                for re in rust_edges:
                    try:
                        edges.append(Edge(
                            source=uuid.UUID(re.source),
                            target=uuid.UUID(re.target),
                            weight=re.weight
                        ))
                    except ValueError:
                        continue
                result[nid] = edges
            else:
                missing.append(nid)
        
        if missing:
            l2_map = self.storage.fetch_neighbors(missing)
            result.update(l2_map)
            
        return result

    def ingest(self, vector: np.ndarray, metadata: dict = None, significance: float = 1.0) -> uuid.UUID:
        """
        Add a new node (Zero-Copy Bridge: L2 Buffer + Immediate Rust L1).
        """
        if not self._started:
            self.start()
        
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        vector = vector.astype(np.float32)
        
        node = Node(
            id=uuid.uuid4(),
            vector=vector,
            energy=0.0,
            last_update=int(time.time()),
            significance=significance,
            metadata=metadata or {}
        )
        
        # 1. Write to L2 via Buffer
        self.node_buffer.mark_dirty(node)
        # 2. IMMEDIATE push to Rust L1
        self._update_rust_l1([node])
        
        return node.id
    
    def connect(self, source_id: uuid.UUID, target_id: uuid.UUID, weight: float, metadata: dict = None) -> None:
        """Create edge."""
        if not self._started:
            self.start()
        
        edge = Edge(
            source=source_id,
            target=target_id,
            weight=weight,
            metadata=metadata or {}
        )
        
        self.edge_buffer.mark_dirty(edge)
        self._update_rust_l1_edges([edge])
    
    def flush(self) -> int:
        return self.node_buffer.flush() + self.edge_buffer.flush()
    
    def close(self) -> None:
        self.node_buffer.stop()
        self.edge_buffer.stop()
        self.flush()
        self._started = False
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
