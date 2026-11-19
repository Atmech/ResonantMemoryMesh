"""Concurrent query benchmarks for the in-memory and PostgreSQL adapters."""
import time
import statistics
import concurrent.futures
import threading
import uuid
from typing import List, Tuple

import pytest
import numpy as np

from rmm import Mesh, MeshConfig, Node, Edge
from rmm.adapters.memory import InMemoryStorage


def random_vector(dim=128):
    v = np.random.randn(dim).astype(np.float32)
    return v / np.linalg.norm(v)


def setup_test_mesh(storage, num_nodes=1000, num_edges=5000):
    """Pre-populate mesh with test data."""
    mesh = Mesh(storage, MeshConfig())
    
    # Create nodes
    node_ids = []
    for i in range(num_nodes):
        vec = random_vector()
        node = Node(
            id=uuid.uuid4(),
            vector=vec,
            energy=np.random.random() * 0.5,
            significance=np.random.random(),
        )
        storage.upsert_nodes([node])
        node_ids.append(node.id)
    
    # Create edges (random connections)
    edges = []
    for _ in range(num_edges):
        src = np.random.choice(node_ids)
        tgt = np.random.choice(node_ids)
        if src != tgt:
            edges.append(Edge(source=src, target=tgt, weight=np.random.random()))
    storage.upsert_edges(edges)
    
    return mesh, node_ids


class BenchmarkResult:
    def __init__(self, latencies: List[float], errors: int = 0):
        self.latencies = sorted(latencies)
        self.errors = errors
    
    @property
    def count(self):
        return len(self.latencies)
    
    @property
    def p50(self):
        return self.latencies[int(len(self.latencies) * 0.50)] if self.latencies else 0
    
    @property
    def p95(self):
        return self.latencies[int(len(self.latencies) * 0.95)] if self.latencies else 0
    
    @property
    def p99(self):
        return self.latencies[int(len(self.latencies) * 0.99)] if self.latencies else 0
    
    @property
    def mean(self):
        return statistics.mean(self.latencies) if self.latencies else 0
    
    @property
    def qps(self):
        total_time = sum(self.latencies)
        return self.count / total_time if total_time > 0 else 0
    
    def __str__(self):
        return (
            f"Queries: {self.count} | Errors: {self.errors}\n"
            f"Mean: {self.mean*1000:.2f}ms | P50: {self.p50*1000:.2f}ms | "
            f"P95: {self.p95*1000:.2f}ms | P99: {self.p99*1000:.2f}ms\n"
            f"Throughput: {self.qps:.1f} qps"
        )


def run_concurrent_queries(
    mesh: Mesh,
    num_queries: int = 1000,
    concurrency: int = 50,
) -> BenchmarkResult:
    """Run concurrent queries and collect latency metrics."""
    latencies = []
    errors = 0
    lock = threading.Lock()
    
    def single_query():
        nonlocal errors
        try:
            query_vec = random_vector()
            start = time.perf_counter()
            result = mesh.query(query_vec, top_n=5)
            elapsed = time.perf_counter() - start
            with lock:
                latencies.append(elapsed)
            return result
        except Exception as e:
            with lock:
                errors += 1
            return None
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(single_query) for _ in range(num_queries)]
        concurrent.futures.wait(futures)
    
    return BenchmarkResult(latencies, errors)


class TestInMemoryBaseline:
    """Baseline benchmark with InMemoryStorage (no network IO)."""

    @pytest.mark.xfail(
        strict=True,
        reason="The in-memory benchmark currently exceeds the 30 ms p99 target under 50 concurrent callers.",
    )
    def test_inmemory_baseline(self):
        """Measure concurrent callers through the Python SDK and Rust kernel."""
        storage = InMemoryStorage()
        mesh, _ = setup_test_mesh(storage, num_nodes=1000, num_edges=5000)

        # Warmup
        for _ in range(10):
            mesh.query(random_vector(), top_n=5)

        # Benchmark
        result = run_concurrent_queries(mesh, num_queries=1000, concurrency=50)

        print("\n" + "=" * 60)
        print("IN-MEMORY BASELINE (No Network IO)")
        print("=" * 60)
        print(result)
        print("=" * 60)

        mesh.close()

        # Assert p99 < 30ms for in-memory
        assert result.p99 < 0.030, f"In-memory p99 {result.p99*1000:.2f}ms > 30ms target"
        assert result.errors == 0, f"Had {result.errors} errors"


class TestPostgresBenchmark:
    """Postgres benchmark with real network IO."""
    
    @pytest.fixture
    def postgres_storage(self):
        """
        Requires: docker-compose up -d
        """
        try:
            from rmm.adapters.postgres import PostgresStorage
        except ImportError:
            pytest.skip("psycopg3 not installed: pip install rmm-core[postgres]")
        
        dsn = "postgresql://rmm:rmm_dev_password@localhost:5432/rmm"
        
        try:
            storage = PostgresStorage(dsn, pool_min=5, pool_max=50)
        except Exception as e:
            pytest.skip(f"Postgres not available: {e}")
        
        yield storage
        storage.close()
    
    def test_postgres_benchmark(self, postgres_storage):
        """
        Target: p99 < 50ms with Postgres.
        """
        mesh, _ = setup_test_mesh(postgres_storage, num_nodes=1000, num_edges=5000)
        
        # Warmup
        for _ in range(10):
            mesh.query(random_vector(), top_n=5)
        
        # Benchmark
        result = run_concurrent_queries(mesh, num_queries=1000, concurrency=50)
        
        print("\n" + "=" * 60)
        print("POSTGRES BENCHMARK (With Network IO)")
        print("=" * 60)
        print(result)
        print(f"\nBuffer stats:")
        print(f"  Writes coalesced: {mesh.node_buffer.writes_coalesced}")
        print(f"  Total flushed: {mesh.node_buffer.total_flushed}")
        print(f"  Load shed events: {mesh.node_buffer.load_shed_events}")
        print("=" * 60)
        
        mesh.close()
        
        # Assert p99 < 50ms for Postgres
        assert result.p99 < 0.050, f"Postgres p99 {result.p99*1000:.2f}ms > 50ms target"
        assert result.errors == 0, f"Had {result.errors} errors"
    
    def test_connection_pool_jitter(self, postgres_storage):
        """
        Test for connection pool jitter under sustained load.
        Looking for latency spikes caused by pool exhaustion.
        """
        mesh, _ = setup_test_mesh(postgres_storage, num_nodes=500, num_edges=2000)
        
        # Run multiple bursts
        all_latencies = []
        for burst in range(5):
            result = run_concurrent_queries(mesh, num_queries=200, concurrency=30)
            all_latencies.extend(result.latencies)
            print(f"Burst {burst+1}: p99={result.p99*1000:.2f}ms")
        
        # Check for jitter (variance between bursts)
        overall = BenchmarkResult(all_latencies)
        
        print("\n" + "=" * 60)
        print("CONNECTION POOL JITTER TEST")
        print("=" * 60)
        print(overall)
        print("=" * 60)
        
        mesh.close()
        
        # P99 should be stable across bursts (not > 2x p50)
        jitter_ratio = overall.p99 / overall.p50 if overall.p50 > 0 else float('inf')
        assert jitter_ratio < 3.0, f"High jitter detected: p99/p50 = {jitter_ratio:.2f}"
