"""
RMM Tests - Mesh SDK integration tests.
"""
import pytest
import uuid
import numpy as np

from rmm import Mesh, MeshConfig, Node, Edge
from rmm.adapters.memory import InMemoryStorage


@pytest.fixture
def storage():
    return InMemoryStorage()


@pytest.fixture
def mesh(storage):
    m = Mesh(storage, MeshConfig())
    yield m
    m.close()


def random_vector(dim=128):
    v = np.random.randn(dim).astype(np.float32)
    return v / np.linalg.norm(v)


class TestMeshIngest:
    
    def test_ingest_creates_node(self, mesh, storage):
        """ingest() should create a node in the buffer."""
        vector = random_vector()
        node_id = mesh.ingest(vector, metadata={"text": "hello"})
        
        assert isinstance(node_id, uuid.UUID)
        
        # Force flush
        mesh.flush()
        
        # Node should exist in storage
        node = storage.get_node(node_id)
        assert node is not None
        assert np.isclose(np.linalg.norm(node.vector), 1.0, atol=1e-6)
    
    def test_ingest_with_significance(self, mesh, storage):
        """ingest() should respect significance parameter."""
        vector = random_vector()
        node_id = mesh.ingest(vector, significance=0.8)
        
        mesh.flush()
        
        node = storage.get_node(node_id)
        assert node.significance == 0.8


class TestMeshConnect:
    
    def test_connect_creates_edge(self, mesh, storage):
        """connect() should create an edge in the buffer."""
        # Create two nodes
        v1 = random_vector()
        v2 = random_vector()
        n1 = mesh.ingest(v1)
        n2 = mesh.ingest(v2)
        
        # Connect them
        mesh.connect(n1, n2, weight=0.75)
        
        mesh.flush()
        
        # Edge should exist
        neighbors = storage.fetch_neighbors([n1])
        edges = neighbors.get(n1, [])
        assert len(edges) == 1
        assert edges[0].target == n2
        assert edges[0].weight == 0.75


class TestMeshQuery:
    
    def test_query_returns_result(self, mesh, storage):
        """query() should return QueryResult with nodes and rationale."""
        # Add some nodes directly to storage
        for i in range(5):
            vec = random_vector()
            node = Node(id=uuid.uuid4(), vector=vec, energy=0.5)
            storage.upsert_nodes([node])
        
        # Query
        query_vec = random_vector()
        result = mesh.query(query_vec, top_n=3)
        
        assert result is not None
        assert isinstance(result.rationale, str)
        assert len(result.entry_ids) <= 3
    
    def test_hybrid_ignition_ranking(self, mesh, storage):
        """Hybrid Ignition should rank by combined similarity + significance."""
        # Create two nodes with same direction but different significance
        base_vec = random_vector()
        
        node_low_sig = Node(id=uuid.uuid4(), vector=base_vec.copy(), significance=0.1)
        node_high_sig = Node(id=uuid.uuid4(), vector=base_vec.copy(), significance=1.0)
        
        storage.upsert_nodes([node_low_sig, node_high_sig])
        
        # Query with base_vec (both have same similarity)
        result = mesh.query(base_vec, top_n=2)
        
        # High significance should rank first
        # (With alpha=0.7: both have same similarity, so (1-alpha)*significance wins)
        if len(result.entry_ids) == 2:
            assert result.entry_ids[0] == node_high_sig.id


class TestMeshContextManager:
    
    def test_context_manager(self, storage):
        """Mesh should work as context manager."""
        with Mesh(storage, MeshConfig()) as mesh:
            node_id = mesh.ingest(random_vector())
            assert node_id is not None
        
        # After exiting, flush should have happened
        assert storage.get_node(node_id) is not None
