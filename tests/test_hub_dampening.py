import numpy as np
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage

def test_hub_dampening():
    storage = InMemoryStorage()
    config = MeshConfig(hub_threshold=5, hub_dampening_alpha=1.0, auto_link=False)
    
    with Mesh(storage, config) as mesh:
        # Create a hub node
        v_hub = np.random.randn(128).astype(np.float32)
        v_hub = v_hub / np.linalg.norm(v_hub)
        id_hub = mesh.ingest(v_hub)
        
        # Create many connections to simulate a hub
        for _ in range(20):
            v_leaf = np.random.randn(128).astype(np.float32)
            v_leaf = v_leaf / np.linalg.norm(v_leaf)
            id_leaf = mesh.ingest(v_leaf)
            mesh.connect(id_hub, id_leaf, weight=0.9)
            mesh.connect(id_leaf, id_hub, weight=0.9)
            
        mesh.flush()
        
        res = mesh.query(v_hub, top_n=5)
        assert len(res.nodes) > 0
        node_ids = [n.id for n in res.nodes]
        assert id_hub in node_ids
