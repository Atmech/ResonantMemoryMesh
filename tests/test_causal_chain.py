import logging
import pytest
import numpy as np
import time
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage
from uuid import UUID

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CausalChain")

# --- BENCHMARK CONSTANTS ---
BETA = 0.7
LAMBDA_DECAY = 0.1
EPSILON_THRESHOLD = 0.005 # Allows 5 hops

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def create_orthogonal_vector(base_vector, seed=42):
    """Create a vector orthogonal-ish to base_vector (< 0.3 similarity)."""
    np.random.seed(seed)
    for _ in range(100):
        v = np.random.randn(128).astype(np.float32)
        v = v / np.linalg.norm(v)
        sim = cosine_similarity(base_vector, v)
        if abs(sim) < 0.2: # Careful strictness
            return v
    return np.random.randn(128).astype(np.float32) # Fallback

def test_causal_chain_benchmark():
    """
    2-Group Comparison — energy propagation over a hand-built causal graph.

    SCOPE OF THIS TEST
    ------------------
    This test demonstrates that RMM's energy-propagation physics can traverse a
    hand-constructed, manually-wired causal chain (1->2->3->4->5) and surface
    Node 5 even though Node 5 is nearly orthogonal to the query vector.

    It does NOT demonstrate:
    - Automatic graph construction from raw text (edges are added by hand).
    - A re-ranked RAG baseline (no Group B is implemented here).
    - Sub-millisecond latency in any general setting.

    Groups implemented:
    Group A: Raw vector search (cosine similarity only) — expected to miss Node 5.
    Group C: RMM Mesh resonance over the hand-built graph — expected to find Node 5.
    """
    storage = InMemoryStorage()
    config = MeshConfig(
        beta=BETA,
        lambda_decay=LAMBDA_DECAY,
        epsilon=EPSILON_THRESHOLD,
        max_hops=5,
        auto_link=False
    )
    
    with Mesh(storage, config) as mesh:
        # --- 1. DATASET CONSTRUCTION ---
        # Query Vector (fixed seed for reproducibility)
        np.random.seed(12345)
        q_vec = np.random.randn(128).astype(np.float32)
        q_vec = q_vec / np.linalg.norm(q_vec)
        
        # Node 1: Entry Point (High Similarity to Query)
        # "Project X is managed by Officer Chen."
        v1 = q_vec + (np.random.randn(128) * 0.05).astype(np.float32) # Very close
        v1 = v1 / np.linalg.norm(v1)
        
        # Node 5: The Goal (Orthogonal to Query)
        # "Titan Corp is currently facing a hostile takeover by Mars Capital."
        v5 = create_orthogonal_vector(q_vec, seed=999)
        
        # Filler Nodes (v2, v3, v4) - varying vectors, doesn't matter much for RAG
        v2 = create_orthogonal_vector(q_vec, seed=2)
        v3 = create_orthogonal_vector(q_vec, seed=3)
        v4 = create_orthogonal_vector(q_vec, seed=4)
        
        # Ingest
        id1 = mesh.ingest(v1, metadata={'label': "Node 1: Officer Chen"}, significance=1.0)
        id2 = mesh.ingest(v2, metadata={'label': "Node 2: Sub-Zero"}, significance=1.0)
        id3 = mesh.ingest(v3, metadata={'label': "Node 3: Arctic Trust"}, significance=1.0)
        id4 = mesh.ingest(v4, metadata={'label': "Node 4: Titan Corp"}, significance=1.0)
        id5 = mesh.ingest(v5, metadata={'label': "Node 5: Mars Capital"}, significance=1.0)
        
        # Connect Chain: 1 -> 2 -> 3 -> 4 -> 5
        mesh.connect(id1, id2, weight=0.9)
        mesh.connect(id2, id3, weight=0.9)
        mesh.connect(id3, id4, weight=0.9)
        mesh.connect(id4, id5, weight=0.9)
        
        # Add "Distractor" Nodes for RAG (Semantically close to Query but noise)
        for i in range(50):
            vd = q_vec + (np.random.rand(128) * 0.4).astype(np.float32) # 0.6-0.8 similarity
            vd = vd / np.linalg.norm(vd)
            mesh.ingest(vd, metadata={'label': f"Distractor {i}"}, significance=0.5)
            
        print("\n[Benchmark] Dataset Constructed.")
        print(f"Query <-> Node 1 Sim: {cosine_similarity(q_vec, v1):.4f}")
        print(f"Query <-> Node 5 Sim: {cosine_similarity(q_vec, v5):.4f} (Must be < 0.3)")
        
        assert cosine_similarity(q_vec, v5) < 0.3, "Poisoned Entry: Node 5 is too similar!"
        
        # --- GROUP A: RAW RAG ---
        print("\n--- Group A: Raw RAG (Vector Search) ---")
        # Standard vector search top_k=50
        candidates_a = mesh.storage.vector_search(q_vec, top_k=50)
        
        rank_a = -1
        if id5 in candidates_a:
            rank_a = candidates_a.index(id5) + 1
            print(f"Node 5 Rank: {rank_a}")
        else:
            print("Node 5 NOT FOUND in Top-50")
            
        # Expectation: Fail (Rank > 10 or Not Found)
        # Because we added 50 distractors closer than Node 5
        assert rank_a == -1 or rank_a > 10, "Group A Failed: RAG accidentally found Node 5"
        
        # --- GROUP C: RMM MESH ---
        print("\n--- Group C: RMM Mesh (Resonance) ---")
        # Ensure L1 is synced (Atomic Pulse)
        mesh.flush() 
        
        print(f"DEBUG: Storage Nodes: {len(mesh.storage.nodes)}")
        print(f"DEBUG: Storage Adjacency Keys: {len(mesh.storage.adjacency)}")
        if len(mesh.storage.adjacency) > 0:
            print(f"DEBUG: Adjacency[id1]: {len(mesh.storage.adjacency.get(id1, []))}")
        
        print(f"DEBUG: id1 = {id1}")

        assert len(mesh.storage.adjacency) > 0, "Storage Adjacency is Empty! Flush failed?"

        # Query
        top_n = 5
        t0 = time.perf_counter()
        res = mesh.query(q_vec, top_n=top_n)
        dt = (time.perf_counter() - t0) * 1000

        print(f"Latency: {dt:.2f} ms")
        print("Results:")

        found_c = False
        rank_c = -1
        for i, node in enumerate(res.nodes):
            label = node.metadata.get('label', 'Mn')
            print(f" {i+1}. [{str(node.id)[:8]}] {label} (E={node.energy:.4f})")
            
            if node.id == id1:
                print(f"   -> FOUND ENTRY NODE 1 at Rank {i+1}")
            
            if node.id == id5:
                found_c = True
                rank_c = i + 1
                
        if found_c:
            print(f"Node 5 Rank: {rank_c}")
            print("SUCCESS: Causal Chain Detected!")
        else:
            print("Node 5 NOT FOUND")
            
        # --- VERDICT ---
        # 1. Successful Retrieval: Node 5 must appear somewhere in the result set.
        # Note: mesh.query() returns ALL nodes that received energy via BFS (not
        # limited to top_n). top_n only gates the Hybrid Ignition entry-point
        # selection. The energy-propagation phase can activate many more nodes.
        # So rank_c is the actual rank within res.nodes (could be > top_n).
        assert found_c, "Group C Failed: RMM did not find Node 5 anywhere in the result set"
        print(f"Node 5 found at rank {rank_c} in a result set of {len(res.nodes)} nodes.")

        # 2. Second query (for observational purposes only — not a latency assertion)
        t0 = time.perf_counter()
        res_hot = mesh.query(q_vec, top_n=top_n)
        dt_hot = (time.perf_counter() - t0) * 1000
        print(f"Second query latency: {dt_hot:.2f} ms (informational only)")
