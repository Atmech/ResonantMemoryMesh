# RMM Rust kernel

The `rmm_rust` extension provides the query kernel and in-memory cache used by the Python SDK. [Build instructions](../README.md#try-the-mesh)

[Kernel traversal](src/kernel.rs) initializes the selected seeds, accumulates transfers across each frontier, and rescales the final activation scores when their total exceeds the configured limit. [Activation and decay](src/physics.rs) defines the clipping rule analyzed in the paper. [Cache](src/cache.rs) stores node records and adjacency lists.

The evaluation fixes the Python and Rust configuration for each query and records the resulting paragraph rankings. [Evaluation protocol](../eval/README.md)
