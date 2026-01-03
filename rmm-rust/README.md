# RMM-Rust: High-Performance Kernel

Rust implementation of the Resonant Memory Mesh AtomicPing algorithm with Python bindings.

## Why Rust?

Python's GIL causes **930x performance degradation** under concurrent load:

| Metric | Python Sequential | Python Concurrent (50 threads) |
|--------|------------------|-------------------------------|
| P99    | 0.91ms           | 845ms                         |

Rust eliminates this bottleneck with:
- **DashMap**: Lock-free concurrent L1 cache
- **Rayon**: Parallel neighbor processing per hop
- **PyO3**: Zero-overhead Python bindings

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Python SDK (rmm-core)                   │
│                  Mesh.query() / ingest() / connect()        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    rmm_rust (PyO3 FFI)                      │
├─────────────────────────────────────────────────────────────┤
│  RustKernel.execute()                                       │
│    └── Parallel BFS with Rayon                              │
│         └── DashMap L1Cache (lock-free reads)               │
│              └── physics.rs (inline accumulate/activate)    │
└─────────────────────────────────────────────────────────────┘
```

## Building

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install maturin
pip install maturin

# Build and install
cd rmm-rust
maturin develop --release
```

## Usage

```python
from rmm_rust import RustKernel, KernelConfig, L1Cache, RustNode

# Create L1 cache and populate
cache = L1Cache()
cache.upsert_node(RustNode(id="...", vector=[...], energy=0.5, ...))

# Create kernel
config = KernelConfig()
config.beta = 0.5
config.max_hops = 5

kernel = RustKernel(config)

# Execute (entirely in Rust, no GIL)
results = kernel.execute(["entry-uuid-1", "entry-uuid-2"], cache)
```

## Target Performance

| Metric | Target |
|--------|--------|
| Concurrent p99 | < 20ms |
| Throughput | > 1,000 qps (8-core) |
