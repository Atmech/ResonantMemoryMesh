"""
RMM BaseStorage - Abstract base class for storage adapters.

Defines the contract for all storage backends (Memory, Postgres, etc.)
"""
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import numpy as np

from rmm import Node, Edge


class BaseStorage(ABC):
    """Abstract base for RMM storage adapters."""
    
    @abstractmethod
    def get_node(self, node_id: uuid.UUID) -> Optional[Node]:
        """Fetch single node by ID."""
        pass
    
    @abstractmethod
    def batch_get_nodes(self, node_ids: List[uuid.UUID]) -> Dict[uuid.UUID, Node]:
        """Batch fetch nodes by IDs."""
        pass
    
    @abstractmethod
    def upsert_nodes(self, nodes: List[Node]) -> None:
        """Batch upsert nodes (Last-Write-Wins by timestamp)."""
        pass
    
    @abstractmethod
    def upsert_edges(self, edges: List[Edge]) -> None:
        """Batch upsert edges (Last-Write-Wins by source/target key)."""
        pass
    
    @abstractmethod
    def delete_nodes(self, node_ids: List[uuid.UUID]) -> None:
        """Delete nodes by IDs (required for Sleep Cycle)."""
        pass
    
    @abstractmethod
    def fetch_neighbors(self, node_ids: List[uuid.UUID]) -> Dict[uuid.UUID, List[Edge]]:
        """Batch fetch outgoing edges for given node IDs."""
        pass
    
    @abstractmethod
    def vector_search(self, query_vector: np.ndarray, top_k: int) -> List[uuid.UUID]:
        """
        ANN search for entry point selection.
        
        Returns node IDs ranked by similarity to query_vector.
        """
        pass
    
    @abstractmethod
    def get_all_nodes(self) -> List[Node]:
        """Fetch all nodes (for testing/debugging)."""
        pass
