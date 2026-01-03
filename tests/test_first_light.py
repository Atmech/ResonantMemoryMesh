
import pytest
import time
import numpy as np
import uuid
import os
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage

class SimulatedPostgresStorage(InMemoryStorage):
    """InMemoryStorage with artificial latency to verify Architectural Isolation."""
    def batch_get_nodes(self, ids):
        time.sleep(0.05) # 50ms DB Latency
        return super().batch_get_nodes(ids)
    
    def fetch_neighbors(self, ids):
        time.sleep(0.05) # 50ms DB Latency
        return super().fetch_neighbors(ids)

# Use strict configuration for testing
def test_first_light_performance():
    """
    First Light: Verify End-to-End Flow and Cold vs Hot Latency.
    Directive: Hot query must be >10x faster than Cold.
    """
    storage = SimulatedPostgresStorage()
    config = MeshConfig(
        buffer_flush_ms=5000, # Large flush to keep things in buffer/RAM mostly
        max_hops=2
    )

    with Mesh(storage, config) as mesh:
        # 1. Ingest Data (Structure)
        print("\n[Light] Ingesting 100 nodes...")
        vectors = []
        ids = []
        for i in range(100):
            v = np.random.rand(128).astype(np.float32)
            v = v / np.linalg.norm(v)
            uid = mesh.ingest(v, significance=1.0)
            vectors.append(v)
            ids.append(uid)
            
        # Create Loop/Edges
        print("[Light] Connecting nodes...")
        for i in range(99):
            mesh.connect(ids[i], ids[i+1], weight=0.9)
        mesh.connect(ids[99], ids[0], weight=0.9) # Cycle
        
        # 2. Force Cold State
        # Ensure data is in L2 (Storage) before clearing L1
        print("[Light] Flushing buffers to Storage...")
        mesh.flush()
        
        # Ingest populates L1. We must CLEAR L1 to simulate restart/cold cache.
        print("[Light] Clearing L1 Cache (Simulating Cold Start)...")
        mesh.cache.clear()
        
        # Verify L1 is empty
        assert mesh.cache.node_count() == 0, "L1 Cache should be empty"
        
        # 3. Cold Query
        q_vec = vectors[0] # Should hit node 0
        
        print("[Light] Executing COLD query...")
        t0 = time.perf_counter()
        res_cold = mesh.query(q_vec, top_n=1)
        t1 = time.perf_counter()
        cold_latency = (t1 - t0) * 1000
        
        print(f"[Light] COLD Latency: {cold_latency:.2f} ms")
        print(f"   -> Result IDs: {res_cold.entry_ids}")
        assert len(res_cold.nodes) > 0, "Cold query returned no nodes (Fault-In failed)"
        
        # 4. Hot Query
        # L1 should now be populated by Fault-In
        print("[Light] Executing HOT query...")
        t0 = time.perf_counter()
        res_hot = mesh.query(q_vec, top_n=1)
        t1 = time.perf_counter()
        hot_latency = (t1 - t0) * 1000
        
        print(f"[Light] HOT Latency:  {hot_latency:.2f} ms")
        
        # 5. Verify Performance Wall
        ratio = cold_latency / (hot_latency + 1e-9)
        print(f"[Light] Speedup: {ratio:.1f}x")
        
        assert ratio > 10.0, f"Failed Success Metric: Hot path only {ratio:.1f}x faster (Need 10x)"
        
        # 6. Verify Resonance Logic (Did we traverse?)
        # With 2 hops and high weight, we should see neighbors
        # entry node is ids[0]. neighbor is ids[1].
        found_ids = [n.id for n in res_hot.nodes]
        assert ids[0] in found_ids, "Entry node not in result"
        # We might see neighbors if energy transferred
        print(f"   -> Activated {len(found_ids)} nodes.")
