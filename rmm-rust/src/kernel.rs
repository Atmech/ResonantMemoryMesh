//! RMM Kernel - AtomicPing BFS implementation
//!
//! The core algorithm implemented in Rust for maximum performance.
//! Uses Rayon for parallel neighbor processing within each hop.
//!
//! Performance optimizations:
//! - f32 for all physics (SIMD-friendly)
//! - Raw bytes UUID support (zero-copy from Python)
//! - DashMap for global cache, FxHashMap for query-local overlay
//! - Rayon parallel iteration for neighbor processing

use pyo3::prelude::*;
use pyo3::types::PyBytes;
use dashmap::DashMap;
use rayon::prelude::*;
use rustc_hash::FxHashMap;
use uuid::Uuid;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use std::collections::HashSet;

use crate::cache::L1Cache;
use crate::models::{RustNode, InternalNode, InternalEdge};
use crate::physics::{apply_decay, accumulate, activate, apply_inhibition};

/// Kernel configuration (all f32 for consistency)
#[pyclass]
#[derive(Clone, Debug)]
pub struct KernelConfig {
    #[pyo3(get, set)]
    pub beta: f32,           // Dissipative Gain
    
    #[pyo3(get, set)]
    pub lambda_decay: f32,   // Decay rate
    
    #[pyo3(get, set)]
    pub max_hops: usize,     // BFS depth limit
    
    #[pyo3(get, set)]
    pub e_max: f32,          // Heat Death limit
    
    #[pyo3(get, set)]
    pub epsilon: f32,        // Minimum energy threshold
    
    #[pyo3(get, set)]
    pub max_neighbors: usize, // Max neighbors per hop
    
    #[pyo3(get, set)]
    pub min_weight: f32,     // Minimum edge weight
    
    // Hub Dampening
    #[pyo3(get, set)]
    pub hub_threshold: u32,
    
    #[pyo3(get, set)]
    pub hub_dampening_alpha: f32,
}

#[pymethods]
impl KernelConfig {
    #[new]
    pub fn new() -> Self {
        KernelConfig {
            beta: 0.5,
            lambda_decay: 0.1,
            max_hops: 5,
            e_max: 10.0,
            epsilon: 0.01,
            max_neighbors: 50,
            min_weight: 0.05,
            hub_threshold: 100,
            hub_dampening_alpha: 0.5,
        }
    }
}

impl Default for KernelConfig {
    fn default() -> Self {
        Self::new()
    }
}

/// The high-performance Rust kernel
#[pyclass]
pub struct RustKernel {
    config: KernelConfig,
}

#[pymethods]
impl RustKernel {
    #[new]
    pub fn new(config: KernelConfig) -> Self {
        RustKernel { config }
    }
    
    /// Execute AtomicPing with string UUIDs (convenience method)
    pub fn execute(
        &self,
        entry_ids: Vec<String>,
        cache: &L1Cache,
        t_now: Option<i64>,
    ) -> Vec<RustNode> {
        let t_now = t_now.unwrap_or_else(|| current_timestamp());
        
        // Parse entry IDs
        let entry_uuids: Vec<Uuid> = entry_ids
            .iter()
            .filter_map(|s| Uuid::parse_str(s).ok())
            .collect();
        
        self.execute_internal(&entry_uuids, cache, t_now)
    }
    
    /// Execute AtomicPing with raw UUID bytes (zero-copy path)
    /// 
    /// Python usage:
    ///   result = kernel.execute_raw([node.id.bytes for node in entries], cache)
    pub fn execute_raw(
        &self,
        py: Python<'_>,
        entry_ids_bytes: Vec<&PyBytes>,
        cache: &L1Cache,
        t_now: Option<i64>,
    ) -> Vec<RustNode> {
        let t_now = t_now.unwrap_or_else(|| current_timestamp());
        
        // Parse raw bytes to UUIDs (no string parsing!)
        let entry_uuids: Vec<Uuid> = entry_ids_bytes
            .iter()
            .filter_map(|bytes| {
                let b = bytes.as_bytes();
                if b.len() == 16 {
                    Some(Uuid::from_bytes(b.try_into().unwrap()))
                } else {
                    None
                }
            })
            .collect();
        
        self.execute_internal(&entry_uuids, cache, t_now)
    }
    
    /// Get config
    pub fn get_config(&self) -> KernelConfig {
        self.config.clone()
    }
}

impl RustKernel {
    /// Internal BFS execution (shared by both string and raw bytes paths)
    fn execute_internal(
        &self,
        entry_ids: &[Uuid],
        cache: &L1Cache,
        t_now: i64,
    ) -> Vec<RustNode> {
        let results = self.execute_bfs(entry_ids, cache, t_now);
        results.into_iter().map(|n| RustNode::from(&n)).collect()
    }
    
    /// The core BFS algorithm - runs entirely in Rust
    /// 
    /// Uses FxHashMap for query-local overlay (single query, no cross-thread access)
    /// Uses DashMap for global L1Cache (many concurrent queries)
    fn execute_bfs(
        &self,
        entry_ids: &[Uuid],
        cache: &L1Cache,
        t_now: i64,
    ) -> Vec<InternalNode> {
        // 1. Initialization
        // Query-local overlay: FxHashMap (faster than DashMap for single-query use)
        let mut overlay: FxHashMap<Uuid, InternalNode> = FxHashMap::default();
        let mut touched_nodes: HashSet<Uuid> = HashSet::new();
        let mut visited_sources: HashSet<Uuid> = HashSet::new();
        
        // Get Arc references to global cache
        let nodes_ref = cache.nodes_ref();
        let adjacency_ref = cache.adjacency_ref();
        
        // Sort entry IDs for determinism
        let mut sorted_entries = entry_ids.to_vec();
        sorted_entries.sort_by_key(|u| u.as_u128());
        
        // Load entry nodes and apply initial decay
        let mut frontier: Vec<Uuid> = Vec::new();
        
        for eid in &sorted_entries {
            if let Some(node_ref) = nodes_ref.get(eid) {
                let mut node = node_ref.value().clone();
                
                // Apply LazySync Decay
                node.energy = apply_decay(
                    node.energy,
                    node.last_update,
                    t_now,
                    self.config.lambda_decay,
                );
                node.last_update = t_now;
                
                // INJECT INITIAL ENERGY (Ignition)
                // Entry nodes start with maximum energy scaled by significance
                node.energy = self.config.e_max * node.significance;
                
                overlay.insert(*eid, node);
                touched_nodes.insert(*eid);
                frontier.push(*eid);
            }
        }
        
        // 2. Layered BFS
        for _hop in 0..self.config.max_hops {
            if frontier.is_empty() {
                break;
            }
            
            // Collect energy transfers from parallel processing
            let transfers: Vec<(Uuid, f32)> = frontier
                .par_iter()
                .flat_map(|source_id| {
                    let source_energy = match overlay.get(source_id) {
                        Some(node) => node.energy,
                        None => return vec![],
                    };
                    
                    // Get neighbors from global cache
                    let edges = adjacency_ref
                        .get(source_id)
                        .map(|e| e.value().clone())
                        .unwrap_or_default();
                    
                    // Calculate degree before edges is moved
                    let degree = edges.len() as f32;
                    
                    // Filter and sort edges
                    let mut valid_edges: Vec<_> = edges
                        .into_iter()
                        .filter(|e| e.weight >= self.config.min_weight)
                        .collect();
                    
                    // Sort: weight DESC, target ASC (determinism)
                    valid_edges.sort_by(|a, b| {
                        b.weight.partial_cmp(&a.weight)
                            .unwrap_or(std::cmp::Ordering::Equal)
                            .then_with(|| a.target.cmp(&b.target))
                    });
                    
                    // Take top N
                    valid_edges.truncate(self.config.max_neighbors);
                    
                    // Degree-aware Hub Dampening
                    let mut gamma = 1.0;
                    if degree > self.config.hub_threshold as f32 {
                        gamma = 1.0 / (1.0 + self.config.hub_dampening_alpha * (degree / self.config.hub_threshold as f32).ln());
                    }
                    
                    // Calculate energy transfers
                    valid_edges
                        .into_iter()
                        .filter_map(|edge| {
                            let mut e_transferred = accumulate(
                                source_energy,
                                edge.weight,
                                self.config.beta,
                            );
                            
                            // Apply hub dampening to the outgoing energy
                            e_transferred *= gamma;
                            
                            if e_transferred >= self.config.epsilon {
                                Some((edge.target, e_transferred))
                            } else {
                                None
                            }
                        })
                        .collect::<Vec<_>>()
                })
                .collect();
            
            // Aggregate energy transfers by target
            let mut buffer_map: FxHashMap<Uuid, f32> = FxHashMap::default();
            for (target, energy) in transfers {
                *buffer_map.entry(target).or_insert(0.0) += energy;
            }
            
            // Commit layer (deterministic order)
            let mut targets: Vec<Uuid> = buffer_map.keys().cloned().collect();
            targets.sort_by_key(|u| u.as_u128());
            
            let mut next_frontier: Vec<Uuid> = Vec::new();
            
            for target_id in targets {
                let energy_input = buffer_map[&target_id];
                
                // Fetch target if not in overlay
                if !overlay.contains_key(&target_id) {
                    if let Some(node_ref) = nodes_ref.get(&target_id) {
                        let mut node = node_ref.value().clone();
                        
                        // Apply LazySync (only once per query)
                        if !touched_nodes.contains(&target_id) {
                            node.energy = apply_decay(
                                node.energy,
                                node.last_update,
                                t_now,
                                self.config.lambda_decay,
                            );
                            node.last_update = t_now;
                            touched_nodes.insert(target_id);
                        }
                        
                        overlay.insert(target_id, node);
                    }
                }
                
                // Apply activation
                if let Some(node) = overlay.get_mut(&target_id) {
                    node.energy = activate(node.energy, energy_input);
                }
                
                // Add to next frontier if not visited as source
                if !visited_sources.contains(&target_id) {
                    next_frontier.push(target_id);
                }
            }
            
            // Mark current frontier as visited
            for id in &frontier {
                visited_sources.insert(*id);
            }
            
            frontier = next_frontier;
        }
        
        // 3. Competitive Inhibition
        let mut result_nodes: Vec<InternalNode> = overlay.into_values().collect();
        let mut energies: Vec<f32> = result_nodes.iter().map(|n| n.energy).collect();
        apply_inhibition(&mut energies, self.config.e_max, self.config.epsilon);
        
        // Apply inhibited energies back
        for (node, &energy) in result_nodes.iter_mut().zip(energies.iter()) {
            node.energy = energy;
        }
        
        result_nodes
    }
}

/// Get current Unix timestamp
fn current_timestamp() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_kernel_creation() {
        let config = KernelConfig::new();
        let kernel = RustKernel::new(config);
        assert_eq!(kernel.config.max_hops, 5);
    }
    
    #[test]
    fn test_config_f32() {
        let config = KernelConfig::new();
        assert_eq!(config.beta, 0.5f32);
        assert_eq!(config.e_max, 10.0f32);
    }
}
