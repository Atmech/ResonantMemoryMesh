//! RMM-Rust: High-Performance Resonant Memory Mesh Kernel
//!
//! This crate provides a Rust implementation of the AtomicPing algorithm
//! with Python bindings via PyO3. Designed for high-concurrency scenarios
//! where Python's GIL becomes a bottleneck.
//!
//! # Architecture
//! - L1 Cache: DashMap for lock-free concurrent reads
//! - Parallelism: Rayon for intra-query neighbor processing
//! - FFI: PyO3 for zero-overhead Python integration

mod models;
mod physics;
mod kernel;
mod cache;

use pyo3::prelude::*;

/// Initialize the rmm_rust Python module
#[pymodule]
fn rmm_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    // Initialize logging bridge
    pyo3_log::init();
    
    // Register classes
    m.add_class::<models::RustNode>()?;
    m.add_class::<models::RustEdge>()?;
    m.add_class::<kernel::RustKernel>()?;
    m.add_class::<cache::L1Cache>()?;
    m.add_class::<kernel::KernelConfig>()?;
    
    // Module metadata
    m.add("__version__", "0.1.0")?;
    
    Ok(())
}
