//! RMM Physics - Pure mathematical functions for energy dynamics
//!
//! These functions are the hot path of the AtomicPing algorithm.
//! Implemented in Rust with f32 for SIMD optimization.
//!
//! Using f32 enables:
//! - 2x more values per cache line
//! - SIMD auto-vectorization (4x f32 per 128-bit register)
//! - Sufficient precision for "fuzzy" neural activation

/// Apply temporal decay to node energy
/// Formula: E_now = E_stored * exp(-lambda * delta_t)
#[inline(always)]
pub fn apply_decay(energy: f32, t_last: i64, t_now: i64, lambda_decay: f32) -> f32 {
    let delta_t = (t_now - t_last).max(0) as f32;
    if delta_t == 0.0 {
        return energy;
    }
    energy * (-lambda_decay * delta_t).exp()
}

/// Linearly accumulate energy from source node across edge
/// Formula: E_transferred = E_source * beta * W_ij
#[inline(always)]
pub fn accumulate(energy_source: f32, weight: f32, beta: f32) -> f32 {
    energy_source * beta * weight
}

/// Apply activation clamp
/// Formula: max(0.0, min(1.0, E_target + E_input))
#[inline(always)]
pub fn activate(energy_target: f32, energy_input: f32) -> f32 {
    (energy_target + energy_input).clamp(0.0, 1.0)
}

/// Apply Competitive Inhibition to prevent Heat Death
/// Scales down all nodes if total active energy exceeds E_max
/// Returns the scale factor applied (1.0 if no scaling needed)
/// 
/// SIMD-friendly: operates on contiguous f32 slice
pub fn apply_inhibition(
    energies: &mut [f32],
    e_max: f32,
    epsilon: f32,
) -> f32 {
    // Sum active energy (SIMD auto-vectorizable)
    let active_energy: f32 = energies
        .iter()
        .filter(|&&e| e >= epsilon)
        .sum();
    
    if active_energy > e_max {
        let scale_factor = e_max / active_energy;
        // Scale all (SIMD auto-vectorizable)
        for energy in energies.iter_mut() {
            *energy *= scale_factor;
        }
        scale_factor
    } else {
        1.0
    }
}

/// Batch accumulate energies (SIMD-optimized)
/// 
/// For a source with N neighbors, computes all transfers at once.
#[inline]
pub fn batch_accumulate(
    energy_source: f32,
    weights: &[f32],
    beta: f32,
) -> Vec<f32> {
    weights.iter().map(|&w| energy_source * beta * w).collect()
}

/// Cosine similarity between two vectors
/// SIMD-friendly dot product
#[inline]
pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    if a.len() != b.len() {
        return 0.0;
    }
    
    // SIMD auto-vectorizable
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    
    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        dot / (norm_a * norm_b)
    }
}

/// Batch dot products for vector search (SIMD-optimized)
pub fn batch_cosine_similarity(query: &[f32], candidates: &[Vec<f32>]) -> Vec<f32> {
    let query_norm: f32 = query.iter().map(|x| x * x).sum::<f32>().sqrt();
    if query_norm == 0.0 {
        return vec![0.0; candidates.len()];
    }
    
    candidates.iter().map(|candidate| {
        let dot: f32 = query.iter().zip(candidate.iter()).map(|(a, b)| a * b).sum();
        let cand_norm: f32 = candidate.iter().map(|x| x * x).sum::<f32>().sqrt();
        if cand_norm == 0.0 {
            0.0
        } else {
            dot / (query_norm * cand_norm)
        }
    }).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_decay() {
        let energy = 1.0f32;
        let result = apply_decay(energy, 0, 10, 0.1);
        assert!((result - 0.36787945).abs() < 1e-5);  // f32 precision
    }
    
    #[test]
    fn test_accumulate() {
        let result = accumulate(1.0, 0.8, 0.5);
        assert!((result - 0.4).abs() < 1e-6);
    }
    
    #[test]
    fn test_activate_clamp() {
        assert_eq!(activate(0.9, 0.2), 1.0);
        assert_eq!(activate(-0.5, 0.3), 0.0);
    }
    
    #[test]
    fn test_inhibition() {
        let mut energies = vec![0.5f32, 0.5, 0.5, 0.5]; // Total = 2.0
        let scale = apply_inhibition(&mut energies, 1.0, 0.01);
        assert!((scale - 0.5).abs() < 1e-6);
        assert!(energies.iter().all(|&e| (e - 0.25).abs() < 1e-6));
    }
    
    #[test]
    fn test_batch_accumulate() {
        let weights = vec![0.5, 0.8, 0.3];
        let result = batch_accumulate(1.0, &weights, 0.5);
        assert!((result[0] - 0.25).abs() < 1e-6);
        assert!((result[1] - 0.40).abs() < 1e-6);
        assert!((result[2] - 0.15).abs() < 1e-6);
    }
}
