"""RMM Quickstart — Bob/Alice causal chain in <20 lines."""
import numpy as np
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage

def embed(text: str, dim: int = 128) -> np.ndarray:
    """Deterministic pseudo-embedding for demo purposes."""
    rng = np.random.RandomState(abs(hash(text)) % (2**31))
    v = rng.randn(dim).astype(np.float32)
    return v / np.linalg.norm(v)

mesh = Mesh(InMemoryStorage(), MeshConfig(beta=0.7, lambda_decay=0.1))

facts = [
    "Bob was recently hired as Managing Director at Mars Capital.",
    "Mars Capital led the Series A for Alice's startup, TechCorp.",
    "TechCorp's product relies on hardware from Quantum Silicon.",
    "Quantum Silicon was acquired by Apex Holdings.",
    "Apex Holdings has an exclusive contract with Omega Inc.",
]
ids = [mesh.ingest(embed(f), metadata={"fact": f}) for f in facts]
for i in range(len(ids) - 1):
    mesh.connect(ids[i], ids[i + 1], weight=0.9)

result = mesh.query(embed("Does Bob have any connection to Omega Inc?"), top_n=10)
for rank, node in enumerate(result.nodes, 1):
    print(f"  Rank {rank}: {node.metadata['fact'][:60]}... (energy: {node.energy:.4f})")
