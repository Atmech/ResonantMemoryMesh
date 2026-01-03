"""
RMM AtomicPing Kernel v2.1

Implements layered BFS energy propagation with:
- Deterministic commit order (sorted buffer_map)
- Visited sources set (cycle prevention)
- LazySync decay on first touch
"""
import time
import uuid
from typing import List, Dict, Set

from rmm import Node
from rmm.adapters.base import BaseStorage
from rmm.core.physics import apply_decay, accumulate, activate, apply_inhibition


class AtomicPing:
    """Atomic Ping kernel for energy propagation."""
    
    def __init__(self, storage: BaseStorage, config=None):
        self.storage = storage
        # Configuration (can be overridden via config)
        self.beta = 0.5  # Dissipative Gain
        self.lambda_decay = 0.1
        self.max_hops = 5
        self.e_max = 10.0  # Heat Death Limit
        self.epsilon = 0.01
        
        if config:
            self.beta = getattr(config, 'beta', self.beta)
            self.lambda_decay = getattr(config, 'lambda_decay', self.lambda_decay)
            self.max_hops = getattr(config, 'max_hops', self.max_hops)
            self.e_max = getattr(config, 'e_max', self.e_max)
            self.epsilon = getattr(config, 'epsilon', self.epsilon)

    def execute(self, entry_ids: List[uuid.UUID], t_now: int = None) -> List[Node]:
        """
        Execute Atomic Ping algorithm.
        
        Returns final state of modified nodes (virtual overlay).
        """
        if t_now is None:
            t_now = int(time.time())

        # 1. Initialization
        overlay: Dict[uuid.UUID, Node] = {}
        touched_nodes: Set[uuid.UUID] = set()
        # v2.1 Spec: Track visited sources to prevent Echo vulnerability
        visited_sources: Set[uuid.UUID] = set()

        # Load entry nodes and apply initial decay
        entry_ids = sorted(entry_ids)  # Deterministic order
        frontier: List[uuid.UUID] = []

        for eid in entry_ids:
            node_orig = self.storage.get_node(eid)
            if node_orig:
                # Clone for query isolation
                node_copy = Node(
                    id=node_orig.id,
                    vector=node_orig.vector.copy(),
                    energy=node_orig.energy,
                    last_update=node_orig.last_update,
                    significance=node_orig.significance
                )
                
                # Apply LazySync Decay
                node_copy.energy = apply_decay(
                    node_copy.energy, node_copy.last_update, t_now, self.lambda_decay
                )
                node_copy.last_update = t_now
                
                overlay[eid] = node_copy
                touched_nodes.add(eid)
                frontier.append(eid)

        # 2. Layered BFS
        for hop in range(self.max_hops):
            if not frontier:
                break
            
            # Batch fetch neighbors
            neighbors_map = self.storage.fetch_neighbors(frontier)
            
            # Energy accumulation buffer
            buffer_map: Dict[uuid.UUID, float] = {}
            next_frontier_candidates: Set[uuid.UUID] = set()

            for source_id in frontier:
                if source_id not in overlay:
                    continue
                
                source_node = overlay[source_id]
                edges = neighbors_map.get(source_id, [])
                
                # Filter & Sort: weight >= 0.05, sorted by weight desc, target asc
                valid_edges = [e for e in edges if e.weight >= 0.05]
                valid_edges.sort(key=lambda e: (-e.weight, e.target.int))
                valid_edges = valid_edges[:50]
                
                for edge in valid_edges:
                    target_id = edge.target
                    
                    # Calculate energy transfer
                    e_transferred = accumulate(source_node.energy, edge.weight, self.beta)
                    
                    if e_transferred >= self.epsilon:
                        if target_id not in buffer_map:
                            buffer_map[target_id] = 0.0
                        buffer_map[target_id] += e_transferred
                        # v2.1: Only add to frontier if not already visited as source
                        if target_id not in visited_sources:
                            next_frontier_candidates.add(target_id)

            # Commit Layer
            # v2.1 Spec: "Commit in deterministic order: sorted by target_id"
            for target_id in sorted(buffer_map.keys()):
                energy_input = buffer_map[target_id]
                
                # Fetch if not in overlay
                if target_id not in overlay:
                    node_orig = self.storage.get_node(target_id)
                    if not node_orig:
                        continue
                    
                    node_copy = Node(
                        id=node_orig.id,
                        vector=node_orig.vector.copy(),
                        energy=node_orig.energy,
                        last_update=node_orig.last_update,
                        significance=node_orig.significance
                    )
                    # Apply LazySync (only once per query)
                    if target_id not in touched_nodes:
                        node_copy.energy = apply_decay(
                            node_copy.energy, node_copy.last_update, t_now, self.lambda_decay
                        )
                        node_copy.last_update = t_now
                        touched_nodes.add(target_id)
                    
                    overlay[target_id] = node_copy
                
                # Apply Activation
                target_node = overlay[target_id]
                target_node.energy = activate(target_node.energy, energy_input)

            # Update frontier for next hop
            # v2.1: Mark current frontier as visited sources
            visited_sources.update(frontier)
            frontier = list(next_frontier_candidates)
            
        # 3. Competitive Inhibition (Heat Death)
        active_nodes = [n for n in overlay.values() if n.energy >= self.epsilon]
        apply_inhibition(active_nodes, self.e_max, self.epsilon)
        
        return list(overlay.values())
