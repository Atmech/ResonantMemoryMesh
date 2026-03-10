# Installation

To use the Resonant Memory Mesh (RMM), you must install both the **Rust Kernel** (for high-performance graph traversals) and the **Python SDK** (for an easy-to-use API).

## Prerequisites

Before installing RMM, ensure you have the following tools available:

-   **Python 3.9+:** We recommend using a virtual environment (e.g., `venv` or `conda`).
-   **Rust Toolchain:** Since the core computational logic is written in Rust, you'll need `cargo` and `rustc`. Install via [rustup.rs](https://rustup.rs).
-   **Maturin:** A build system for Rust Python extensions. Install it globally or in your virtual environment: `pip install maturin`.

## Step 1: Building the Rust Kernel

The RMM kernel (`rmm-rust`) handles the complex graph algorithms and energy propagation. 

Navigate to the rust kernel directory and compile it into a Python wheel using `maturin`:

```bash
cd rmm-rust

# Compile a release build for maximum performance
maturin develop --release
```

This will compile the Rust source code and automatically install the resulting Python module (`rmm_rust`) into your active Python environment.

## Step 2: Installing the Python SDK

The RMM Core (`rmm-core`) provides the user-facing `Mesh` interface, storage adapters (like Postgres and InMemory), and LLM integration helpers.

Navigate to the `rmm-core` directory and install the package:

```bash
cd ../rmm-core

# Install the package and its dependencies
pip install .

# For development installations with testing tools:
# pip install -e ".[dev]"
```

## Step 3: Verifying the Installation

Open a Python REPL or script and try importing the Mesh:

```python
from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage

# Initialize an empty mesh
storage = InMemoryStorage()
mesh = Mesh(storage, MeshConfig(beta=0.7))

print("RMM successfully installed and initialized!")
```

If this script runs without errors, your environment is ready to begin constructing Resonant Memory Meshes.
