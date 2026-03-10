# Rust Kernel Internals

At the heart of the Resonant Memory Mesh is `rmm-rust`, a highly optimized computational engine designed to process non-Euclidean graph traversals with sub-millisecond latency.

While the Python SDK (`rmm-core`) manages the user-facing API and database interactions, the heavy lifting of the "Resonance Pulse" happens entirely inside the Rust Kernel.

## Architecture

The `rmm-rust` system utilizes **PyO3** to expose zero-cost Python bindings. When you call `mesh.query()` from Python, the array and edge state are passed across the Foreign Function Interface (FFI) to the Rust kernel.

1.  **Initial Activation (Vector Similarity):**
    Before graph traversal begins, the system needs starting points. The Rust kernel (or the underlying Postgres DB if using a persistent adapter) computes the traditional Cosine Similarity between your `query_vector` and every node in the mesh.
    
    Nodes that cross a predefined similarity threshold (or the top K nodes) are injected with an initial energy payload proportional to their similarity score.

2.  **Topological Propagation (The Physics of Reasoning):**
    This is the core execution loop. You can think of it like heat radiating through metal conductors.
    
    The kernel executes an iterative, breadth-first expansion across the graph's edges. For each activated node `i`, "heat" (energy) is passed to its neighbors `j` according to the physical properties of the connection:
    
    `E_new(j) = E_old(j) + [ E(i) * W(i->j) * beta * S(i) ]`
    
    -   **`E(i)`:** The current energy of the source node (how "hot" it is).
    -   **`W(i->j)` (Edge Weight):** The conductivity of the edge (e.g., 0.9 is a thick copper wire, 0.1 is a frayed string).
    -   **`beta` (Gain):** The system-wide tuning parameter. If `beta` is high, the entire network conducts easily.
    -   **`S(i)` (Significance):** An intrinsic multiplier. If node `i` is a "core memory" (Significance 2.0), it amplifies the energy passing through it.

    This traversal happens incredibly fast within the Rust engine, calculating thousands of these state changes per millisecond.

3.  **Global Decay (`lambda`):**
    After each propagation step (or "hop"), a global decay factor ($\lambda$) is applied to all active nodes to prevent infinite positive feedback loops. Once the energy delta on the graph drops below a stable threshold, the resonance pulse completes.

## High-Performance Tuning

The Kernel provides two primary levers for controlling the depth of RMM's reasoning: `beta` and `lambda_decay`.

### `beta` (Propagation Gain)
-   **Default:** `0.7`
-   **High (`>0.85`):** Causes "hallucinatory" memory. Energy flows extremely freely, and distant, tangential concepts will bubble up to the surface. Useful for expansive, creative brainstorming agents.
-   **Low (`<0.3`):** Causes "strict" memory. The system behaves similarly to standard RAG, rarely moving beyond direct semantic matches.

### `lambda_decay` (Energy Attenuation)
-   **Default:** `0.5`
-   **High (`>0.8`):** Energy bleeds out quickly. Limits traversal to roughly 1 or 2 hops.
-   **Low (`<0.2`):** Energy lingers, allowing the pulse to traverse incredibly deep, 5+ hop causal chains. Be warned: exceptionally low decay combined with highly interconnected graphs can cause performance bottlenecks as the kernel attempts to process the entire mesh simultaneously.

## Compiling for Production

When building `rmm-rust` for deployment, always ensure you use the `--release` flag. Development builds of the Rust kernel can be orders of magnitude slower due to the lack of LLVM optimizations.

```bash
cargo build --release  # For standalone testing
maturin develop --release  # For Python bindings
```
