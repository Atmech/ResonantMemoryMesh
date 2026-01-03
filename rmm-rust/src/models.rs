//! RMM Models - Node and Edge structs with Python bindings
//!
//! These are Rust-native data structures that can be shared
//! across threads without GIL contention.
//!
//! Performance: Using f32 for energy/physics to enable SIMD optimization.

use pyo3::prelude::*;
use pyo3::types::PyBytes;
use uuid::Uuid;

/// A memory node in the mesh
/// 
/// Using f32 for energy to enable SIMD vectorization in physics.
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustNode {
    #[pyo3(get)]
    pub id: String,  // UUID as string for Python compatibility
    
    #[pyo3(get)]
    pub label: String, // Short semantic summary (max 128 chars)
    
    pub vector: Vec<f32>,  // L2-normalized embedding
    
    #[pyo3(get, set)]
    pub energy: f32,  // f32 for SIMD
    
    #[pyo3(get, set)]
    pub last_update: i64,
    
    #[pyo3(get, set)]
    pub significance: f32,
}

#[pymethods]
impl RustNode {
    #[new]
    pub fn new(
        id: String,
        label: String,
        vector: Vec<f32>,
        energy: f32,
        last_update: i64,
        significance: f32,
    ) -> Self {
        // Truncate label to 128 chars
        let truncated_label = if label.len() > 128 {
            label[..128].to_string()
        } else {
            label
        };

        RustNode {
            id,
            label: truncated_label,
            vector,
            energy,
            last_update,
            significance,
        }
    }
    
    /// Create from raw UUID bytes (zero-copy path)
    #[staticmethod]
    pub fn from_bytes(
        py: Python<'_>,
        uuid_bytes: &PyBytes,
        label: String,
        vector: Vec<f32>,
        energy: f32,
        last_update: i64,
        significance: f32,
    ) -> PyResult<Self> {
        let bytes = uuid_bytes.as_bytes();
        if bytes.len() != 16 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "UUID bytes must be exactly 16 bytes"
            ));
        }
        let uuid = Uuid::from_bytes(bytes.try_into().unwrap());
        
        // Truncate label to 128 chars
        let truncated_label = if label.len() > 128 {
            label[..128].to_string()
        } else {
            label
        };

        Ok(RustNode {
            id: uuid.to_string(),
            label: truncated_label,
            vector,
            energy,
            last_update,
            significance,
        })
    }
    
    /// Get vector as Python list
    #[getter]
    pub fn vector(&self) -> Vec<f32> {
        self.vector.clone()
    }
    
    /// Get UUID as raw bytes for zero-copy passing
    pub fn id_bytes(&self, py: Python<'_>) -> PyResult<PyObject> {
        let uuid = Uuid::parse_str(&self.id)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(PyBytes::new(py, uuid.as_bytes()).into())
    }
    
    /// Clone the node (for overlay isolation)
    pub fn clone_node(&self) -> RustNode {
        self.clone()
    }
}

impl RustNode {
    /// Parse UUID from string
    pub fn uuid(&self) -> Uuid {
        Uuid::parse_str(&self.id).unwrap_or_else(|_| Uuid::nil())
    }
    
    /// Get vector L2 norm
    pub fn vector_norm(&self) -> f32 {
        self.vector.iter().map(|x| x * x).sum::<f32>().sqrt()
    }
}

/// An edge connecting two nodes
#[pyclass]
#[derive(Clone, Debug)]
pub struct RustEdge {
    #[pyo3(get)]
    pub source: String,
    
    #[pyo3(get)]
    pub target: String,
    
    #[pyo3(get, set)]
    pub weight: f32,
}

#[pymethods]
impl RustEdge {
    #[new]
    pub fn new(source: String, target: String, weight: f32) -> PyResult<Self> {
        if weight < 0.0 || weight > 1.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                format!("Edge weight must be [0.0, 1.0], got {}", weight)
            ));
        }
        Ok(RustEdge { source, target, weight })
    }
    
    /// Create from raw UUID bytes
    #[staticmethod]
    pub fn from_bytes(
        py: Python<'_>,
        source_bytes: &PyBytes,
        target_bytes: &PyBytes,
        weight: f32,
    ) -> PyResult<Self> {
        let src = uuid_from_bytes(source_bytes)?;
        let tgt = uuid_from_bytes(target_bytes)?;
        Ok(RustEdge {
            source: src.to_string(),
            target: tgt.to_string(),
            weight,
        })
    }
}

/// Helper: Parse UUID from PyBytes
fn uuid_from_bytes(bytes: &PyBytes) -> PyResult<Uuid> {
    let b = bytes.as_bytes();
    if b.len() != 16 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "UUID bytes must be exactly 16 bytes"
        ));
    }
    Ok(Uuid::from_bytes(b.try_into().unwrap()))
}

/// Internal representation for efficient processing
/// All f32 for SIMD-friendly cache lines
#[derive(Clone, Debug)]
pub struct InternalNode {
    pub id: Uuid,
    pub label: String,
    pub vector: Vec<f32>,
    pub energy: f32,
    pub last_update: i64,
    pub significance: f32,
    pub last_accessed: i64, // For V-LRU
}

impl From<&RustNode> for InternalNode {
    fn from(node: &RustNode) -> Self {
        InternalNode {
            id: Uuid::parse_str(&node.id).unwrap_or_else(|_| Uuid::nil()),
            label: node.label.clone(),
            vector: node.vector.clone(),
            energy: node.energy,
            last_update: node.last_update,
            significance: node.significance,
            last_accessed: get_current_time_secs(),
        }
    }
}

impl From<&InternalNode> for RustNode {
    fn from(node: &InternalNode) -> Self {
        RustNode {
            id: node.id.to_string(),
            label: node.label.clone(),
            vector: node.vector.clone(),
            energy: node.energy,
            last_update: node.last_update,
            significance: node.significance,
        }
    }
}

/// Helper for timestamps
fn get_current_time_secs() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64
}

#[derive(Clone, Debug)]
pub struct InternalEdge {
    pub source: Uuid,
    pub target: Uuid,
    pub weight: f32,
}

impl From<&RustEdge> for InternalEdge {
    fn from(edge: &RustEdge) -> Self {
        InternalEdge {
            source: Uuid::parse_str(&edge.source).unwrap_or_else(|_| Uuid::nil()),
            target: Uuid::parse_str(&edge.target).unwrap_or_else(|_| Uuid::nil()),
            weight: edge.weight,
        }
    }
}
