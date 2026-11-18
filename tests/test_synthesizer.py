import pytest
import uuid
from rmm import Node, Edge
from rmm.adapters.memory import InMemoryStorage
from rmm.core.synthesizer import generate_structural_rationale

def test_synthesizer_format():
    storage = InMemoryStorage()
    
    # Create 3 connected nodes
    import numpy as np
    vec = np.zeros(128, dtype=np.float32)
    vec[0] = 1.0
    
    n1 = Node(id=uuid.uuid4(), vector=vec.copy(), energy=0.9)
    n2 = Node(id=uuid.uuid4(), vector=vec.copy(), energy=0.8)
    n3 = Node(id=uuid.uuid4(), vector=vec.copy(), energy=0.7)
    n4 = Node(id=uuid.uuid4(), vector=vec.copy(), energy=0.1) # Ignored
    
    storage.add_node(n1)
    storage.add_node(n2)
    storage.add_node(n3)
    storage.add_node(n4)
    
    storage.add_edge(Edge(source=n1.id, target=n2.id, weight=0.9))
    storage.add_edge(Edge(source=n2.id, target=n3.id, weight=0.8))
    
    # Generate rationale from a set of nodes (e.g. result of kernel)
    result_nodes = [n1, n2, n3, n4]
    
    output = generate_structural_rationale(result_nodes, storage)
    
    print(output)
    
    # Verify content
    # Should contain n1 and n2 id partials
    assert str(n1.id)[:8] in output
    assert str(n2.id)[:8] in output
    assert "0.90" in output # Energy of n1
    assert "0.99" not in output # Weight is 0.9
    assert "--[0.90]-->" in output or "--[0.80]-->" in output
    
    # Count lines: synthesizer outputs 1 confidence header + up to 2 edge lines = max 3 lines
    lines = output.strip().split('\n')
    assert len(lines) <= 3  # [Confidence: ...] header + up to 2 edge lines
    assert len(lines) >= 1

    # Test Truncation
    output_trunc = generate_structural_rationale(result_nodes, storage, max_chars=10)
    assert output_trunc.endswith("...")
