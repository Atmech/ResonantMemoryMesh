//! RMM L1 Cache - Thread-safe in-memory graph storage
//!
//! Shared node and adjacency maps use DashMap shard locks.

use pyo3::prelude::*;
use pyo3::types::PyBytes;
use dashmap::DashMap;
use uuid::Uuid;
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};
use rand::seq::IteratorRandom; 

use crate::models::{RustNode, RustEdge, InternalNode, InternalEdge};

/// Thread-safe L1 Cache for the active mesh
/// 
/// Python SyncThread Integration:
/// - Call `update_batch()` after WriteBackBuffer flushes to Postgres
/// - This keeps Rust L1 in sync with Postgres L2
#[pyclass]
pub struct L1Cache {
    /// Node storage: UUID -> Node
    nodes: Arc<DashMap<Uuid, InternalNode>>,
    
    /// Adjacency list: Source UUID -> Vec<Edge>
    adjacency: Arc<DashMap<Uuid, Vec<InternalEdge>>>,
    
    /// Metrics for monitoring SyncThread health
    update_count: AtomicU64,
    last_sync_timestamp: AtomicU64,
}

#[pymethods]
impl L1Cache {
    #[new]
    pub fn new() -> Self {
        Self::create_new()
    }
    
    // ========================================
    // PYTHON SYNCTHREAD INTERFACE
    // ========================================
    // These methods are called by the Python WriteBackBuffer
    // after it flushes to Postgres, to keep L1 in sync with L2.
    
    /// Batch update nodes from Python SyncThread
    /// 
    /// Called by WriteBackBuffer after successful Postgres flush.
    /// Uses raw bytes for UUIDs to avoid string parsing overhead.
    pub fn update_batch(&self, nodes: Vec<RustNode>) {
        // Enforce Eviction if needed
        self.perform_eviction_if_needed();

        for node in nodes {
            let internal = InternalNode::from(&node);
            self.nodes.insert(internal.id, internal);
        }
        self.update_count.fetch_add(1, Ordering::Relaxed);
    }
    
    /// Batch update nodes using raw UUID bytes
    pub fn update_batch_raw(
        &self,
        py: Python<'_>,
        nodes: Vec<(
            &PyBytes,  // UUID as 16 bytes
            String,    // label
            Vec<f32>,  // vector
            f32,       // energy
            i64,       // last_update
            f32,       // significance
        )>,
    ) -> PyResult<usize> {
        // Enforce Eviction if needed
        self.perform_eviction_if_needed();

        let mut count = 0;
        for (uuid_bytes, label, vector, energy, last_update, significance) in nodes {
            let bytes = uuid_bytes.as_bytes();
            if bytes.len() != 16 {
                continue;
            }
            
            // Truncate label to 128 chars
            let truncated_label = if label.len() > 128 {
                label[..128].to_string()
            } else {
                label
            };

            let uuid = Uuid::from_bytes(bytes.try_into().unwrap());
            let node = InternalNode {
                id: uuid,
                label: truncated_label,
                vector,
                energy,
                last_update,
                significance,
                last_accessed: get_current_time_secs(),
            };
            self.nodes.insert(uuid, node);
            count += 1;
        }
        self.update_count.fetch_add(1, Ordering::Relaxed);
        self.last_sync_timestamp.store(
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            Ordering::Relaxed,
        );
        Ok(count)
    }

    /// Internal: V-LRU Eviction (Sample 16, Cap 1M)
    fn perform_eviction_if_needed(&self) {
        const MAX_NODES: usize = 1_000_000;
        const SAMPLE_SIZE: usize = 16;
        
        if self.nodes.len() < MAX_NODES {
           return;
        }
        
        // V-LRU Logic:
        // Score = Recency / Significance
        // We want to evict the item with the HIGHEST Score (High Recency = Old, Low Significance)
        // Recency = Now - LastAccessed (Larger is older)
        
        let now = get_current_time_secs();
        let mut rng = rand::thread_rng();
        
        // Refined Strategy:
        // Since `dashmap` doesn't support efficient random sampling of keys,
        // and we want to avoid global locks...
        // We accept that we might go slightly over 1M.
        // But we must prune.
        
        // Let's implement a "Lazy Random" approach.
        // We accept that we might go slightly over 1M.
        
        // Let's just collect 16 keys from the beginning of iteration (pseudo-random due to hash map)?
        
        let sample: Vec<Uuid> = self.nodes
            .iter()
            .take(SAMPLE_SIZE * 2) // Take a few more to allow for race conditions
            .map(|r| *r.key())
            .collect();
            
        if sample.is_empty() { return; }
        
        // Find worst candidate
        let mut worst_id = Uuid::nil();
        let mut worst_score = -1.0;
        
        for id in sample {
            if let Some(r) = self.nodes.get(&id) {
                let node = r.value();
                let recency = (now - node.last_accessed) as f32;
                // Avoid div by zero
                let sig = if node.significance < 0.001 { 0.001 } else { node.significance };
                
                let score = recency / sig;
                
                if score > worst_score {
                    worst_score = score;
                    worst_id = id;
                }
            }
        }
        
        if worst_id != Uuid::nil() {
            self.nodes.remove(&worst_id);
            self.adjacency.remove(&worst_id);
            // We leave incoming edges for now to be lazy/fast. (Or we can invoke cleanup later)
        }
    }
    
    /// Batch update edges from Python SyncThread
    pub fn update_edges_batch(&self, edges: Vec<RustEdge>) {
        // Group edges by source for efficient adjacency update
        let mut by_source: std::collections::HashMap<Uuid, Vec<InternalEdge>> = 
            std::collections::HashMap::new();
        
        for edge in edges {
            let internal = InternalEdge::from(&edge);
            by_source
                .entry(internal.source)
                .or_insert_with(Vec::new)
                .push(internal);
        }
        
        // Upsert into adjacency (merge with existing)
        for (source, new_edges) in by_source {
            self.adjacency
                .entry(source)
                .and_modify(|existing| {
                    // Replace edges with same target
                    for new_edge in &new_edges {
                        if let Some(pos) = existing.iter().position(|e| e.target == new_edge.target) {
                            existing[pos] = new_edge.clone();
                        } else {
                            existing.push(new_edge.clone());
                        }
                    }
                })
                .or_insert(new_edges);
        }
    }
    
    /// Delete nodes from cache (called during Sleep Cycle)
    pub fn delete_nodes_batch(&self, ids: Vec<String>) {
        for id_str in ids {
            if let Ok(uuid) = Uuid::parse_str(&id_str) {
                self.nodes.remove(&uuid);
                self.adjacency.remove(&uuid);
                // Also remove edges pointing to this node
                self.adjacency.alter_all(|_, mut edges| {
                    edges.retain(|e| e.target != uuid);
                    edges
                });
            }
        }
    }
    
    /// Delete nodes using raw bytes
    pub fn delete_nodes_raw(&self, py: Python<'_>, ids: Vec<&PyBytes>) -> usize {
        let mut count = 0;
        for uuid_bytes in ids {
            let bytes = uuid_bytes.as_bytes();
            if bytes.len() != 16 {
                continue;
            }
            let uuid = Uuid::from_bytes(bytes.try_into().unwrap());
            if self.nodes.remove(&uuid).is_some() {
                count += 1;
            }
            self.adjacency.remove(&uuid);
        }
        count
    }
    
    // ========================================
    // STANDARD ACCESSORS
    // ========================================
    
    /// Add or update a node
    pub fn upsert_node(&self, node: &RustNode) {
        let internal = InternalNode::from(node);
        self.nodes.insert(internal.id, internal);
    }
    
    /// Batch upsert nodes
    pub fn upsert_nodes(&self, nodes: Vec<RustNode>) {
        for node in nodes {
            self.upsert_node(&node);
        }
    }
    
    /// Get a node by ID (string)
    pub fn get_node(&self, id: String) -> Option<RustNode> {
        let uuid = Uuid::parse_str(&id).ok()?;
        self.nodes.get(&uuid).map(|n| RustNode::from(n.value()))
    }
    
    /// Get a node by raw UUID bytes
    pub fn get_node_raw(&self, py: Python<'_>, uuid_bytes: &PyBytes) -> Option<RustNode> {
        let bytes = uuid_bytes.as_bytes();
        if bytes.len() != 16 {
            return None;
        }
        let uuid = Uuid::from_bytes(bytes.try_into().ok()?);
        self.nodes.get(&uuid).map(|n| RustNode::from(n.value()))
    }
    
    /// Add an edge
    pub fn add_edge(&self, edge: &RustEdge) {
        let internal = InternalEdge::from(edge);
        self.adjacency
            .entry(internal.source)
            .or_insert_with(Vec::new)
            .push(internal);
    }
    
    /// Batch add edges
    pub fn add_edges(&self, edges: Vec<RustEdge>) {
        for edge in edges {
            self.add_edge(&edge);
        }
    }
    
    /// Get neighbors of a node
    pub fn get_neighbors(&self, id: String) -> Vec<RustEdge> {
        let uuid = match Uuid::parse_str(&id) {
            Ok(u) => u,
            Err(_) => return vec![],
        };
        
        self.adjacency
            .get(&uuid)
            .map(|edges| {
                edges.iter().map(|e| RustEdge {
                    source: e.source.to_string(),
                    target: e.target.to_string(),
                    weight: e.weight,
                }).collect()
            })
            .unwrap_or_default()
    }
    
    /// Get node count
    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }
    
    /// Get edge count
    pub fn edge_count(&self) -> usize {
        self.adjacency.iter().map(|r| r.value().len()).sum()
    }
    
    /// Clear all data
    pub fn clear(&self) {
        self.nodes.clear();
        self.adjacency.clear();
    }
    
    // ========================================
    // METRICS (for monitoring SyncThread health)
    // ========================================
    
    /// Get total update batch count
    pub fn get_update_count(&self) -> u64 {
        self.update_count.load(Ordering::Relaxed)
    }
    
    /// Get last sync timestamp
    pub fn get_last_sync_timestamp(&self) -> u64 {
        self.last_sync_timestamp.load(Ordering::Relaxed)
    }
    
    /// Check if cache is stale (no sync in last N seconds)
    pub fn is_stale(&self, max_age_seconds: u64) -> bool {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();
        let last = self.last_sync_timestamp.load(Ordering::Relaxed);
        if last == 0 {
            return true; // Never synced
        }
        now - last > max_age_seconds
    }
}

/// Helper for timestamps
fn get_current_time_secs() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64
}

impl L1Cache {
    /// Rust-internal constructor
    pub fn create_new() -> Self {
        L1Cache {
            nodes: Arc::new(DashMap::new()),
            adjacency: Arc::new(DashMap::new()),
            update_count: AtomicU64::new(0),
            last_sync_timestamp: AtomicU64::new(0),
        }
    }

    /// Internal: Get node reference (for kernel use)
    pub fn get_internal(&self, id: &Uuid) -> Option<InternalNode> {
        self.nodes.get(id).map(|n| n.value().clone())
    }
    
    /// Internal: Get neighbors (for kernel use)
    pub fn get_internal_neighbors(&self, id: &Uuid) -> Vec<InternalEdge> {
        self.adjacency
            .get(id)
            .map(|edges| edges.value().clone())
            .unwrap_or_default()
    }
    
    /// Internal: Batch get neighbors (for BFS)
    pub fn batch_get_neighbors(&self, ids: &[Uuid]) -> Vec<(Uuid, Vec<InternalEdge>)> {
        ids.iter()
            .map(|id| (*id, self.get_internal_neighbors(id)))
            .collect()
    }
    
    /// Get Arc references for kernel
    pub fn nodes_ref(&self) -> Arc<DashMap<Uuid, InternalNode>> {
        Arc::clone(&self.nodes)
    }
    
    pub fn adjacency_ref(&self) -> Arc<DashMap<Uuid, Vec<InternalEdge>>> {
        Arc::clone(&self.adjacency)
    }
}

impl Default for L1Cache {
    fn default() -> Self {
        Self::create_new()
    }
}
