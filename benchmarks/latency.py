"""
RMM Latency Benchmark
=====================
Measures warm sequential query latency and approximate sequential QPS
for an in-memory Mesh with 1000 nodes, 128-dim vectors, no edges (pure
proximity/vector search path through Hybrid Ignition).

Run with:
    .venv/bin/python benchmarks/latency.py
"""

import statistics
import time

import numpy as np

from rmm import Mesh, MeshConfig
from rmm.adapters.memory import InMemoryStorage

# --- Configuration ---
NUM_NODES = 1000
DIM = 128
NUM_WARMUP = 50
NUM_MEASURE = 200
TOP_N = 5


def random_unit_vector(dim=DIM):
    v = np.random.randn(dim).astype(np.float32)
    return v / np.linalg.norm(v)


def main():
    print("RMM Latency Benchmark")
    print(f"  Nodes : {NUM_NODES}")
    print(f"  Dim   : {DIM}")
    print(f"  top_n : {TOP_N}")
    print(f"  Warmup: {NUM_WARMUP} queries")
    print(f"  Timed : {NUM_MEASURE} queries (one caller, sequential)")
    print()

    storage = InMemoryStorage()
    config = MeshConfig(
        auto_link=False,  # no autolinker overhead — pure proximity graph
        adaptive_tuning=False,
    )
    mesh = Mesh(storage, config)

    # --- Populate ---
    print(f"Ingesting {NUM_NODES} nodes...")
    t_ingest_start = time.perf_counter()
    for _ in range(NUM_NODES):
        mesh.ingest(random_unit_vector())
    mesh.flush()
    t_ingest_end = time.perf_counter()
    print(f"  Ingest + flush: {(t_ingest_end - t_ingest_start)*1000:.1f} ms total")
    print()

    # --- Warmup (populate L1 cache via fault-in) ---
    print(f"Warming up ({NUM_WARMUP} queries)...")
    for _ in range(NUM_WARMUP):
        mesh.query(random_unit_vector(), top_n=TOP_N)
    print("  Warmup done.")
    print()

    # --- Measure ---
    print(f"Measuring {NUM_MEASURE} warm queries...")
    latencies_ms = []
    for _ in range(NUM_MEASURE):
        q = random_unit_vector()
        t0 = time.perf_counter()
        mesh.query(q, top_n=TOP_N)
        latencies_ms.append((time.perf_counter() - t0) * 1000)

    latencies_ms.sort()

    def pct(p):
        idx = int(len(latencies_ms) * p)
        return latencies_ms[min(idx, len(latencies_ms) - 1)]

    median_ms = statistics.median(latencies_ms)
    mean_ms = statistics.mean(latencies_ms)
    p95_ms = pct(0.95)
    p99_ms = pct(0.99)
    # Sequential QPS = 1 / mean_latency_in_seconds
    seq_qps = 1000.0 / mean_ms if mean_ms > 0 else 0

    print()
    print("=" * 50)
    print("Results (warm, in-memory, 1000 nodes, one sequential caller)")
    print("=" * 50)
    print(f"  Median latency : {median_ms:.2f} ms")
    print(f"  Mean latency   : {mean_ms:.2f} ms")
    print(f"  P95 latency    : {p95_ms:.2f} ms")
    print(f"  P99 latency    : {p99_ms:.2f} ms")
    print(f"  Sequential QPS : {seq_qps:.0f}")
    print("=" * 50)
    print()
    print("Note: QPS above is for one caller. Concurrent")
    print("throughput under GIL has NOT been benchmarked here.")

    mesh.close()

    return median_ms, seq_qps


if __name__ == "__main__":
    main()
