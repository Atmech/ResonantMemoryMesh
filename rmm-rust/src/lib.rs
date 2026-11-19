//! Python bindings for graph traversal, activation updates, and the shared cache.

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
