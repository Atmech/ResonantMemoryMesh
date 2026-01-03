"""
RMM Synthesizer - Generates structural rationale from resonance results.
"""
from typing import List
from rmm import Node


def generate_structural_rationale(nodes: List[Node], storage, max_chars: int = 1000) -> str:
    """
    Generate Structural Rationale string.
    
    1. Select Top 3 Nodes (Energy Desc, ID Asc)
    2. Select Top 2 Edges connecting selected nodes (Weight Desc)
    3. Format output with Confidence indicator
    """
    if not nodes:
        return "No resonance detected."

    # 1. Top 3 Nodes: Energy Desc, ID Asc
    sorted_nodes = sorted(nodes, key=lambda n: (-n.energy, n.id.int))
    top_nodes = sorted_nodes[:3]
    top_node_ids = {n.id for n in top_nodes}
    
    # 2. Top 2 Edges (between top nodes only)
    candidate_edges = []
    neighbors_map = storage.fetch_neighbors(list(top_node_ids))
    
    for source_id, edges in neighbors_map.items():
        for edge in edges:
            if edge.target in top_node_ids:
                candidate_edges.append(edge)
                
    # Sort: Weight Desc, (Source, Target) Asc
    candidate_edges.sort(key=lambda e: (-e.weight, e.source.int, e.target.int))
    top_edges = candidate_edges[:2]
    
    # 3. Format
    lines = []
    node_map = {n.id: n for n in top_nodes}
    
    for edge in top_edges:
        src = node_map[edge.source]
        tgt = node_map[edge.target]
        line = f"[{str(src.id)[:8]}] {{{src.energy:.2f}}} --[{edge.weight:.2f}]--> [{str(tgt.id)[:8]}] {{{tgt.energy:.2f}}}"
        lines.append(line)
        
    # Fallback if no edges
    if not lines:
        for n in top_nodes:
            lines.append(f"[{str(n.id)[:8]}] {{{n.energy:.2f}}}")
    
    # v2.1 Enhancement: Resonance Strength indicator
    avg_energy = sum(n.energy for n in top_nodes) / len(top_nodes) if top_nodes else 0.0
    if avg_energy >= 0.5:
        confidence = "High"
    elif avg_energy >= 0.2:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    result = f"[Confidence: {confidence}]\n" + "\n".join(lines)
    
    # Truncate
    if len(result) > max_chars:
        result = result[:max_chars-3] + "..."
        
    return result
