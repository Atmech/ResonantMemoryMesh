import numpy as np
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage

def test_autolinker():
    storage = InMemoryStorage()
    # Configuration with autolinker enabled
    config = MeshConfig(auto_link=True, auto_link_threshold=0.8)
    
    with Mesh(storage, config) as mesh:
        # Node 1
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v1 = v1 / np.linalg.norm(v1)
        id1 = mesh.ingest(v1, metadata={'label': 'A'})
        
        # Node 2 (similar to Node 1, dot product 1.0 > 0.8)
        v2 = np.array([1.0, 0.0], dtype=np.float32)
        v2 = v2 / np.linalg.norm(v2)
        id2 = mesh.ingest(v2, metadata={'label': 'B'})
        
        # Node 3 (orthogonal to Node 1 and 2, dot product 0.0 < 0.8)
        v3 = np.array([0.0, 1.0], dtype=np.float32)
        v3 = v3 / np.linalg.norm(v3)
        id3 = mesh.ingest(v3, metadata={'label': 'C'})
        
        mesh.flush()
        
        # Expected: Edge between 1 and 2, no edges to 3
        edges1 = storage.adjacency.get(id1, [])
        edges2 = storage.adjacency.get(id2, [])
        edges3 = storage.adjacency.get(id3, [])
        
        # 1 should link to 2
        assert any(e.target == id2 for e in edges1)
        # 2 should link to 1
        assert any(e.target == id1 for e in edges2)
        # 3 should have 0 edges
        assert len(edges3) == 0
