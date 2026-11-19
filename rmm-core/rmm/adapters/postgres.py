"""
RMM PostgresStorage - PostgreSQL adapter with psycopg3.

Key features:
- Async-capable via psycopg3's C-backend
- Cosine distance for vector search
- CTE-based batch neighbor fetch
- Connection pooling for high concurrency
"""
import uuid
import json
import logging
from typing import Dict, List, Optional
from contextlib import contextmanager

import numpy as np

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool
except ImportError:
    raise ImportError(
        "PostgresStorage requires psycopg3. Install with: pip install rmm-core[postgres]"
    )

from rmm import Node, Edge
from rmm.adapters.base import BaseStorage

logger = logging.getLogger(__name__)


class PostgresStorage(BaseStorage):
    """
    PostgreSQL storage adapter with pgvector extension.
    
    Uses psycopg3 (C-backend) for non-blocking IO.
    
    Args:
        dsn: PostgreSQL connection string
        pool_min: Minimum pool connections (default 2)
        pool_max: Maximum pool connections (default 20)
        vector_dim: Embedding dimension (default 128)
    
    Example:
        storage = PostgresStorage("postgresql://user:pass@localhost/rmm")
        mesh = Mesh(storage, MeshConfig())
    """
    
    def __init__(
        self,
        dsn: str,
        pool_min: int = 2,
        pool_max: int = 20,
        vector_dim: int = 128,
    ):
        self.dsn = dsn
        self.vector_dim = vector_dim
        self.pool = ConnectionPool(
            dsn,
            min_size=pool_min,
            max_size=pool_max,
            kwargs={"row_factory": dict_row}
        )
        logger.info(f"PostgresStorage initialized with pool size {pool_min}-{pool_max}")
    
    @contextmanager
    def _conn(self):
        """Get connection from pool."""
        with self.pool.connection() as conn:
            yield conn
    
    def get_node(self, node_id: uuid.UUID) -> Optional[Node]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, vector, energy, last_update, significance FROM nodes WHERE id = %s",
                (str(node_id),)
            ).fetchone()
        
        if not row:
            return None
        return self._row_to_node(row)
    
    def batch_get_nodes(self, node_ids: List[uuid.UUID]) -> Dict[uuid.UUID, Node]:
        if not node_ids:
            return {}
        
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT id, vector, energy, last_update, significance 
                FROM nodes 
                WHERE id = ANY(%s::uuid[])
                """,
                ([str(nid) for nid in node_ids],)
            ).fetchall()
        
        return {uuid.UUID(row['id']): self._row_to_node(row) for row in rows}
    
    def upsert_nodes(self, nodes: List[Node]) -> None:
        if not nodes:
            return
        
        # Prepare JSONB payload for batch upsert function
        payload = json.dumps([
            {
                'id': str(n.id),
                'vector': n.vector.tolist(),
                'energy': n.energy,
                'last_update': n.last_update,
                'significance': n.significance,
            }
            for n in nodes
        ])
        
        with self._conn() as conn:
            conn.execute("SELECT upsert_nodes(%s::jsonb)", (payload,))
            conn.commit()
    
    def upsert_edges(self, edges: List[Edge]) -> None:
        if not edges:
            return
        
        with self._conn() as conn:
            # Batch INSERT ON CONFLICT
            conn.executemany(
                """
                INSERT INTO edges (source, target, weight, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (source, target) DO UPDATE SET
                    weight = EXCLUDED.weight,
                    metadata = EXCLUDED.metadata
                """,
                [(str(e.source), str(e.target), e.weight, json.dumps(e.metadata)) for e in edges]
            )
            conn.commit()
    
    def delete_nodes(self, node_ids: List[uuid.UUID]) -> None:
        if not node_ids:
            return
        
        with self._conn() as conn:
            # CASCADE will clean up edges
            conn.execute(
                "DELETE FROM nodes WHERE id = ANY(%s::uuid[])",
                ([str(nid) for nid in node_ids],)
            )
            conn.commit()
    
    def fetch_neighbors(self, node_ids: List[uuid.UUID]) -> Dict[uuid.UUID, List[Edge]]:
        if not node_ids:
            return {}
        
        with self._conn() as conn:
            # Use CTE function for optimized batch fetch
            rows = conn.execute(
                "SELECT * FROM fetch_neighbors_batch(%s::uuid[], 0.05, 50)",
                ([str(nid) for nid in node_ids],)
            ).fetchall()
        
        result: Dict[uuid.UUID, List[Edge]] = {nid: [] for nid in node_ids}
        for row in rows:
            source = uuid.UUID(row['source'])
            edge = Edge(
                source=source,
                target=uuid.UUID(row['target']),
                weight=row['weight'],
                metadata=row['metadata'] or {}
            )
            result[source].append(edge)
        
        return result
    
    def vector_search(self, query_vector: np.ndarray, top_k: int) -> List[uuid.UUID]:
        # Normalize query
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm
        
        # Format for pgvector
        vec_str = f"[{','.join(str(x) for x in query_vector.tolist())}]"
        
        with self._conn() as conn:
            # Cosine distance <=> (lower = more similar)
            rows = conn.execute(
                """
                SELECT id FROM nodes
                ORDER BY vector <=> %s::vector
                LIMIT %s
                """,
                (vec_str, top_k)
            ).fetchall()
        
        return [uuid.UUID(row['id']) for row in rows]
    
    def get_all_nodes(self) -> List[Node]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, vector, energy, last_update, significance FROM nodes"
            ).fetchall()
        return [self._row_to_node(row) for row in rows]
    
    def _row_to_node(self, row: dict) -> Node:
        """Convert DB row to Node."""
        vector = np.array(row['vector'], dtype=np.float32)
        # Ensure normalized (DB should store normalized, but verify)
        norm = np.linalg.norm(vector)
        if norm > 0 and not np.isclose(norm, 1.0, atol=1e-6):
            vector = vector / norm
        
        return Node(
            id=uuid.UUID(row['id']) if isinstance(row['id'], str) else row['id'],
            vector=vector,
            energy=row['energy'],
            last_update=row['last_update'],
            significance=row['significance']
        )
    
    def close(self) -> None:
        """Close connection pool."""
        self.pool.close()
