"""
Resonant Memory Mesh - Core Package

An associative memory kernel for AI systems with async persistence.
"""
import numpy as np
import uuid
import time
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Node:
    """Memory node with energy state."""
    id: uuid.UUID
    vector: np.ndarray  # float32[d], L2-normalized
    energy: float = 0.0
    last_update: int = field(default_factory=lambda: int(time.time()))
    significance: float = 1.0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.vector.dtype != np.float32:
            self.vector = self.vector.astype(np.float32)
        norm = np.linalg.norm(self.vector)
        if not np.isclose(norm, 1.0, atol=1e-6):
            raise ValueError(f"Node vector not normalized. Norm: {norm}")


@dataclass
class Edge:
    """Weighted connection between nodes."""
    source: uuid.UUID
    target: uuid.UUID
    weight: float  # [0.0, 1.0]
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not (0.0 <= self.weight <= 1.0):
            raise ValueError(f"Edge weight must be [0.0, 1.0]. Got: {self.weight}")


@dataclass
class MeshConfig:
    """Configuration for Mesh instance."""
    beta: float = 0.5
    lambda_decay: float = 0.1
    max_hops: int = 5
    e_max: float = 10.0
    epsilon: float = 0.01
    buffer_flush_ms: int = 100
    buffer_shards: int = 16
    hybrid_alpha: float = 0.7  # Hybrid Ignition: Similarity weight


@dataclass
class QueryResult:
    """Result from Mesh.query()."""
    nodes: List[Node]
    rationale: str
    entry_ids: List[uuid.UUID] = field(default_factory=list)


# Public API
from rmm.mesh import Mesh
from rmm.adapters.base import BaseStorage

__all__ = ["Node", "Edge", "Mesh", "MeshConfig", "QueryResult", "BaseStorage"]
