import logging
from rmm import MeshConfig

logger = logging.getLogger(__name__)

class AdaptiveTuner:
    """
    Dynamically adjusts Dissipative Gain (beta) and Decay (lambda)
    based on the structural density of the memory mesh.
    """
    
    @staticmethod
    def compute_density(storage) -> float:
        """
        Calculate graph density rho = |E| / (|V| * (|V|-1)).
        Returns None if the storage backend does not expose the required counts.
        """
        if not hasattr(storage, 'nodes') or not hasattr(storage, 'adjacency'):
            return None  # Unsupported storage; caller should skip tuning

        v_count = len(storage.nodes)
        if v_count < 2:
            return 0.0

        e_count = sum(len(edges) for edges in storage.adjacency.values())

        max_edges = v_count * (v_count - 1)
        if max_edges == 0:
            return 0.0
        return float(e_count) / max_edges

    @staticmethod
    def tune(config: MeshConfig, storage) -> MeshConfig:
        """Returns a tuned copy of the configuration."""
        if not getattr(config, 'adaptive_tuning', False):
            return config

        density = AdaptiveTuner.compute_density(storage)
        if density is None:
            logger.warning("AdaptiveTuner: storage backend does not expose node/edge counts; skipping tuning.")
            return config

        k = 2.0  # Sensitivity constant

        beta_adapt = config.beta * (1.0 - density)**k
        lambda_adapt = config.lambda_decay * (1.0 + density)**k

        logger.debug(f"AdaptiveTuner: Density {density:.4f} -> β:{beta_adapt:.4f}, λ:{lambda_adapt:.4f}")
        
        return MeshConfig(
            beta=beta_adapt,
            lambda_decay=lambda_adapt,
            max_hops=config.max_hops,
            e_max=config.e_max,
            epsilon=config.epsilon,
            buffer_flush_ms=config.buffer_flush_ms,
            buffer_shards=config.buffer_shards,
            hybrid_alpha=config.hybrid_alpha,
            hub_threshold=getattr(config, 'hub_threshold', 100),
            hub_dampening_alpha=getattr(config, 'hub_dampening_alpha', 0.5),
            auto_link=getattr(config, 'auto_link', True),
            auto_link_threshold=getattr(config, 'auto_link_threshold', 0.6),
            adaptive_tuning=config.adaptive_tuning
        )
