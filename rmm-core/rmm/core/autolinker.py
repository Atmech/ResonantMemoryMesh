import numpy as np
import uuid
import logging

logger = logging.getLogger(__name__)

class AutoLinker:
    """
    Constructs edges automatically based on vector proximity,
    bypassing the need for LLM-based entity extraction.
    """
    
    @staticmethod
    def link_by_proximity(node_id: uuid.UUID, mesh, threshold: float = 0.6, top_k: int = 10):
        """
        Links a newly ingested node to its semantic neighbors.
        """
        node = mesh.storage.get_node(node_id)
        if not node:
            return
            
        # Vector search
        candidate_ids = mesh.storage.vector_search(node.vector, top_k=top_k + 1)
        
        links_created = 0
        for cid in candidate_ids:
            if cid == node_id:
                continue
            
            target_node = mesh.storage.get_node(cid)
            if not target_node:
                continue
                
            sim = float(np.clip(np.dot(node.vector, target_node.vector), 0.0, 1.0))
            if sim >= threshold:
                # bidirectional link
                mesh.connect(node_id, cid, weight=sim, metadata={'source': 'autolinker'})
                mesh.connect(cid, node_id, weight=sim, metadata={'source': 'autolinker'})
                links_created += 2
                
        if links_created > 0:
            logger.debug(f"AutoLinker: Created {links_created} edges for {node_id}")
