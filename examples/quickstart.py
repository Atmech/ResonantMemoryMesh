"""Trace a query across two explicit links using fixed unit vectors."""
import numpy as np
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage


def main():
    vectors = np.eye(3, dtype=np.float32)
    labels = ["Manufacturer", "Chip supplier", "Acquirer"]
    with Mesh(InMemoryStorage(), MeshConfig(auto_link=False)) as mesh:
        ids = [mesh.ingest(vector, metadata={"label": label})
               for vector, label in zip(vectors, labels)]
        mesh.connect(ids[0], ids[1], weight=0.9)
        mesh.connect(ids[1], ids[2], weight=0.9)
        mesh.flush()

        result = mesh.query(vectors[0], top_n=1)
        print("Activated records from one starting point")
        for node in result.nodes:
            print(f"{node.metadata['label']}: {node.energy:.3f}")


if __name__ == "__main__":
    main()
