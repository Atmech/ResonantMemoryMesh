"""
RMM Physics - Pure mathematical functions for energy dynamics.
"""
import numpy as np


def apply_decay(energy: float, t_last: int, t_now: int, lambda_decay: float = 0.1) -> float:
    """
    Apply temporal decay to node energy.
    
    Formula: E_now = E_stored * exp(-lambda * delta_t)
    """
    delta_t = max(0, t_now - t_last)
    if delta_t == 0:
        return energy
    return float(energy * np.exp(-lambda_decay * delta_t))


def accumulate(energy_source: float, weight: float, beta: float) -> float:
    """
    Linearly accumulate energy from source node across edge.
    
    Formula: E_transferred = E_source * beta * W_ij
    """
    return float(energy_source * beta * weight)


def activate(energy_target_decayed: float, energy_input: float) -> float:
    """
    Apply activation clamp.
    
    Formula: max(0.0, min(1.0, E_target + E_input))
    """
    total = energy_target_decayed + energy_input
    return float(np.clip(total, 0.0, 1.0))


def apply_inhibition(nodes: list, e_max: float = 10.0, epsilon: float = 0.01) -> None:
    """
    Apply Competitive Inhibition to prevent Heat Death.
    
    Scales down all nodes if total active energy exceeds E_max.
    Modifies node objects in-place.
    """
    active_energy = sum(n.energy for n in nodes if n.energy >= epsilon)
    
    if active_energy > e_max:
        scale_factor = e_max / active_energy
        for node in nodes:
            node.energy *= scale_factor
