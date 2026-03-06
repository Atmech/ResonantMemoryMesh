import numpy as np
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage
from rmm.core.adaptive import AdaptiveTuner

def test_adaptive_tuner():
    storage = InMemoryStorage()
    config = MeshConfig(beta=0.5, lambda_decay=0.1, adaptive_tuning=True, auto_link=False)
    
    with Mesh(storage, config) as mesh:
        v1 = np.array([1.0, 0.0], dtype=np.float32)
        v1 /= np.linalg.norm(v1)
        v2 = np.array([0.0, 1.0], dtype=np.float32)
        v2 /= np.linalg.norm(v2)
        
        id1 = mesh.ingest(v1)
        id2 = mesh.ingest(v2)
        mesh.flush()
        
        mesh.connect(id1, id2, 1.0)
        mesh.connect(id2, id1, 1.0)
        mesh.flush()
        
        tuned = AdaptiveTuner.tune(config, storage)
        
        assert tuned.beta < 0.5
        assert tuned.lambda_decay > 0.1
