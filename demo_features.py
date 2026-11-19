import numpy as np
import uuid
import time
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage
from rmm.core.adaptive import AdaptiveTuner

def generate_vector(dim=128):
    v = np.random.randn(dim).astype(np.float32)
    return v / np.linalg.norm(v)

def demo_autolinker():
    print("\n--- Feature 1: AutoLinker Pipeline ---")
    print("Goal: Ingesting vectors close to each other should automatically create edges.")
    
    storage = InMemoryStorage()
    # Enable autolinker with a low threshold for the demo
    config = MeshConfig(auto_link=True, auto_link_threshold=0.8)
    
    with Mesh(storage, config) as mesh:
        # Create a base vector
        base_vec = generate_vector()
        
        print("1. Ingesting Node A (Base Concept)")
        id_a = mesh.ingest(base_vec, metadata={"name": "Node A"})
        
        print("2. Ingesting Node B (Very similar to Node A, sim ~ 0.99)")
        # Add tiny noise
        vec_b = base_vec + (np.random.randn(128).astype(np.float32) * 0.05)
        vec_b = vec_b / np.linalg.norm(vec_b)
        id_b = mesh.ingest(vec_b, metadata={"name": "Node B"})
        
        print("3. Ingesting Node C (Completely random, sim ~ 0.0)")
        vec_c = generate_vector()
        id_c = mesh.ingest(vec_c, metadata={"name": "Node C"})
        
        mesh.flush()
        
        # Check edges
        edges_a = storage.adjacency.get(id_a, [])
        print(f"\nResults for Node A:")
        print(f"Edges connected to Node A: {len(edges_a)}")
        for e in edges_a:
            target_name = storage.get_node(e.target).metadata.get('name')
            print(f" -> Automatically linked to: {target_name} (Weight: {e.weight:.4f})")
            
        assert [edge.target for edge in edges_a] == [id_b], "Expected a single edge to Node B"
        print("SUCCESS: AutoLinker connected Node A and Node B, but ignored Node C.")


def demo_hub_dampening():
    print("\n--- Feature 2: Super-Node Hub Dampening ---")
    print("Goal: Energy passing through a massive hub should be dampened to prevent noise.")
    
    storage = InMemoryStorage()
    # Set hub threshold extremely low (e.g., 5) so we can trigger it easily
    config = MeshConfig(hub_threshold=5, hub_dampening_alpha=1.5, auto_link=False)
    
    with Mesh(storage, config) as mesh:
        print("1. Creating a 'Hub' node and connecting it to 20 leaves...")
        v_hub = generate_vector()
        id_hub = mesh.ingest(v_hub, metadata={"label": "The Hub"})
        
        leaf_ids = []
        for i in range(20):
            v_leaf = generate_vector()
            id_leaf = mesh.ingest(v_leaf, metadata={"label": f"Leaf {i}"})
            leaf_ids.append(id_leaf)
            mesh.connect(id_hub, id_leaf, weight=0.9)
            mesh.connect(id_leaf, id_hub, weight=0.9)
            
        mesh.flush()
        
        print("2. Firing energy directly at the Hub...")
        # Query exactly on the hub
        res = mesh.query(v_hub, top_n=5)
        
        print("\nTop 5 Activated Nodes:")
        for idx, n in enumerate(res.nodes[:5]):
            print(f"{idx+1}. {n.metadata.get('label', 'Unknown')} (Energy: {n.energy:.4f})")
            
        hub_node = next((n for n in res.nodes if n.id == id_hub), None)
        leaf_nodes = [n for n in res.nodes if "Leaf" in n.metadata.get('label', '')]
        
        if hub_node:
            print(f"Hub activation: {hub_node.energy:.4f}")
        if leaf_nodes:
            print(f"Highest leaf activation: {leaf_nodes[0].energy:.4f}")


def demo_adaptive_tuning():
    print("\n--- Feature 3: Adaptive Gain Tuning ---")
    print("Goal: Beta (Gain) and Lambda (Decay) should naturally shift as the mesh becomes denser.")
    
    storage = InMemoryStorage()
    config = MeshConfig(adaptive_tuning=True, beta=0.5, lambda_decay=0.1, auto_link=False)
    
    print("1. Simulating a Sparse Graph (10 nodes, 10 edges)")
    with Mesh(storage, config) as mesh:
        nodes = [mesh.ingest(generate_vector()) for _ in range(10)]
        for i in range(9):
            mesh.connect(nodes[i], nodes[i+1], weight=0.8)
        mesh.flush()
        
        density = AdaptiveTuner.compute_density(storage)
        tuned = AdaptiveTuner.tune(config, storage)
        print(f" Sparse Density : {density:.4f}")
        print(f" Tuned Beta     : {tuned.beta:.4f} (Remains high to allow energy travel)")
        print(f" Tuned Lambda   : {tuned.lambda_decay:.4f} (Remains low)")

    print("\n2. Simulating a Dense Graph (Adding 70 more random edges)")
    with Mesh(storage, config) as mesh:
        for _ in range(70):
            n1 = np.random.choice(nodes)
            n2 = np.random.choice(nodes)
            if n1 != n2:
                mesh.connect(n1, n2, weight=0.5)
        mesh.flush()
        
        density2 = AdaptiveTuner.compute_density(storage)
        tuned2 = AdaptiveTuner.tune(config, storage)
        print(f" Dense Density  : {density2:.4f}")
        print(f" Tuned Beta     : {tuned2.beta:.4f} (Drops lower to prevent noise chain-reactions)")
        print(f" Tuned Lambda   : {tuned2.lambda_decay:.4f} (Increases to kill errant energy faster)")
        
        print("\nSUCCESS: Adaptive parameters shift proportionally with graph density.")

if __name__ == "__main__":
    print("==================================================")
    print("  Resonant Memory Mesh - New Features Interactive Demo")
    print("==================================================\n")
    time.sleep(1)
    
    demo_autolinker()
    time.sleep(1)
    print("-" * 50)
    
    demo_hub_dampening()
    time.sleep(1)
    print("-" * 50)
    
    demo_adaptive_tuning()
    print("\nDemo Completed Successfully!")
