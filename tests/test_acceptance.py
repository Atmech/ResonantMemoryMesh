import pytest
import uuid
import numpy as np
from rmm.core.physics import apply_decay, accumulate, activate, apply_inhibition
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage
from src.kernel import AtomicPing

@pytest.fixture
def storage():
    return InMemoryStorage()

@pytest.fixture
def kernel(storage):
    k = AtomicPing(storage)
    k.beta = 0.5
    k.lambda_decay = 0.1
    k.max_hops = 5
    k.e_max = 10.0
    return k

def create_node(energy=0.0):
    vec = np.zeros(128, dtype=np.float32)
    vec[0] = 1.0 # Ensure normalized
    return Node(id=uuid.uuid4(), vector=vec, energy=energy, last_update=1000)

def test_linear_chain(storage, kernel):
    """
    Test A: Linear Chain
    A(1.0) -> B -> C
    Weight = 1.0, Beta = 0.5
    Expected: B=0.5, C=0.25
    """
    # Setup
    node_a = create_node(energy=1.0)
    node_b = create_node(energy=0.0)
    node_c = create_node(energy=0.0)
    
    # Force timestamps to ensure no decay during test setup
    t_fixed = 1000
    node_a.last_update = t_fixed
    node_b.last_update = t_fixed
    node_c.last_update = t_fixed
    
    storage.add_node(node_a)
    storage.add_node(node_b)
    storage.add_node(node_c)
    
    storage.add_edge(Edge(source=node_a.id, target=node_b.id, weight=1.0))
    storage.add_edge(Edge(source=node_b.id, target=node_c.id, weight=1.0))
    
    # Execute
    # We pass t_now = t_fixed so decay is 0 (delta_t = 0)
    # This isolates the Accumulation logic
    results = kernel.execute([node_a.id], t_now=t_fixed)
    
    res_map = {n.id: n for n in results}
    
    # Check A (original) - Should remain 1.0 (activation clamp) or degrade?
    # Logic: A is entry. Hop 0. 
    # Did we specify A should degrade? No, only moved energy?
    # Spec: "Entry Pointing... Apply LazySync...". 
    # BFS: A is source.
    # Is A's energy consumed? "Dissipative Gain" implies transmitted energy is derived from source.
    # Does source lose energy? Spec doesn't explicitly say "Source -= Sent". 
    # Usually spreading activation *copies* energy or *moves* it.
    # Formula: "E_temp_j = sum(E_source * beta * W)"
    # It calculates *destination* energy. Source energy usually stays unless decayed.
    # So A should be 1.0.
    
    # Check B
    # B = A * beta * W = 1.0 * 0.5 * 1.0 = 0.5
    assert res_map[node_b.id].energy == pytest.approx(0.5, abs=1e-6)
    
    # Check C
    # C = B * beta * W = 0.5 * 0.5 * 1.0 = 0.25
    assert res_map[node_c.id].energy == pytest.approx(0.25, abs=1e-6)

def test_inhibition_scaling(storage, kernel):
    """
    Test B: Inhibitor
    10 nodes, e=0.5, Total=5.0
    E_max=1.0
    Expected: Scale factor 0.2 -> e=0.1
    """
    kernel.e_max = 1.0
    nodes = []
    
    # Create 10 independent nodes
    t_fixed = 1000
    for _ in range(10):
        n = create_node(energy=0.5)
        n.last_update = t_fixed
        storage.add_node(n)
        nodes.append(n)
        
    # Execute with ALL as entry points to ensure they are in the overlay
    # If they are just in storage, they won't be in 'results' unless touched.
    entry_ids = [n.id for n in nodes]
    
    results = kernel.execute(entry_ids, t_now=t_fixed)
    
    for n in results:
        assert n.energy == pytest.approx(0.1, abs=1e-6)

def test_determinism(storage, kernel):
    """
    Test C: Determinism
    Running the same query twice should yield bit-identical results.
    """
    # Setup random graph
    t_fixed = 1000
    root = create_node(energy=1.0)
    root.last_update = t_fixed
    storage.add_node(root)
    
    n1 = create_node(energy=0.0)
    n1.last_update = t_fixed
    storage.add_node(n1)
    
    n2 = create_node(energy=0.0)
    n2.last_update = t_fixed
    storage.add_node(n2)
    
    # Edge with weight that requires sorting
    storage.add_edge(Edge(source=root.id, target=n1.id, weight=0.8))
    storage.add_edge(Edge(source=root.id, target=n2.id, weight=0.9)) # n2 should convert first?
    
    # Run 1
    res1 = kernel.execute([root.id], t_now=t_fixed)
    res1_map = {n.id: n.energy for n in res1}
    
    # Run 2
    res2 = kernel.execute([root.id], t_now=t_fixed)
    res2_map = {n.id: n.energy for n in res2}
    
    assert res1_map == res2_map
    
    # Verify order of results if list is returned
    # The return value is list(overlay.values()). Dictionary order is insertion based in Python 3.7+
    # But for strict determinism, let's check values match exactly.
    for n1_res, n2_res in zip(res1, res2):
        assert n1_res.id == n2_res.id
        assert n1_res.energy == n2_res.energy
