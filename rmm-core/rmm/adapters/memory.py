"""
RMM InMemoryStorage - In-memory storage adapter for testing and prototyping.
"""
import uuid
from typing import Dict, List, Optional

import numpy as np

from rmm import Node, Edge
from rmm.adapters.base import BaseStorage


class InMemoryStorage(BaseStorage):
    """In-memory storage adapter (for testing and prototyping)."""
    
    def __init__(self):
        self.nodes: Dict[uuid.UUID, Node] = {}
        self.adjacency: Dict[uuid.UUID, List[Edge]] = {}
    
    def get_node(self, node_id: uuid.UUID) -> Optional[Node]:
        return self.nodes.get(node_id)
    
    def batch_get_nodes(self, node_ids: List[uuid.UUID]) -> Dict[uuid.UUID, Node]:
        return {nid: self.nodes[nid] for nid in node_ids if nid in self.nodes}
    
    def upsert_nodes(self, nodes: List[Node]) -> None:
        """Upsert nodes with Last-Write-Wins logic."""
        for node in nodes:
            if node.id in self.nodes:
                existing = self.nodes[node.id]
                if node.last_update >= existing.last_update:
                    self.nodes[node.id] = node
            else:
                self.nodes[node.id] = node
    
    def upsert_edges(self, edges: List[Edge]) -> None:
        """Upsert edges (replace by source/target key)."""
        for edge in edges:
            if edge.source not in self.adjacency:
                self.adjacency[edge.source] = []
            
            # Find and replace existing edge with same target
            existing_edges = self.adjacency[edge.source]
            replaced = False
            for i, e in enumerate(existing_edges):
                if e.target == edge.target:
                    existing_edges[i] = edge
                    replaced = True
                    break
            if not replaced:
                existing_edges.append(edge)
    
    def delete_nodes(self, node_ids: List[uuid.UUID]) -> None:
        """Delete nodes and their edges."""
        for nid in node_ids:
            self.nodes.pop(nid, None)
            self.adjacency.pop(nid, None)
            # Also remove edges pointing to this node
            for source_id in list(self.adjacency.keys()):
                self.adjacency[source_id] = [
                    e for e in self.adjacency[source_id] 
                    if e.target != nid
                ]
    
    def fetch_neighbors(self, node_ids: List[uuid.UUID]) -> Dict[uuid.UUID, List[Edge]]:
        return {nid: self.adjacency.get(nid, []) for nid in node_ids}
    
    def vector_search(self, query_vector: np.ndarray, top_k: int) -> List[uuid.UUID]:
        """Brute-force cosine similarity search."""
        if not self.nodes:
            return []
        
        # Normalize query
        query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-9)
        
        scores = []
        for node in self.nodes.values():
            similarity = float(np.dot(query_norm, node.vector))
            scores.append((node.id, similarity))
        
        # Sort by similarity descending
        scores.sort(key=lambda x: -x[1])
        return [s[0] for s in scores[:top_k]]
    
    def get_all_nodes(self) -> List[Node]:
        return list(self.nodes.values())
    
    # Convenience methods for direct adds (not via buffer)
    def add_node(self, node: Node) -> None:
        """Direct add for backwards compatibility."""
        self.upsert_nodes([node])
    
    def add_edge(self, edge: Edge) -> None:
        """Direct add for backwards compatibility."""
        self.upsert_edges([edge])
