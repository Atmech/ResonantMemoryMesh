"""
RMM Tests - Buffer Swap & Release verification.
"""
import time
import threading
import pytest
from unittest.mock import MagicMock, patch
import uuid

from rmm import Node
from rmm.core.buffer import WriteBackBuffer
import numpy as np


def create_test_node(energy=0.0):
    vec = np.zeros(128, dtype=np.float32)
    vec[0] = 1.0
    return Node(id=uuid.uuid4(), vector=vec, energy=energy)


class TestWriteBackBuffer:
    
    def test_coalescing(self):
        """Multiple updates to same node should coalesce to 1 write."""
        written = []
        
        def mock_write(nodes):
            written.extend(nodes)
        
        buffer = WriteBackBuffer(
            storage_write_fn=mock_write,
            key_func=lambda n: n.id,
            num_shards=4
        )
        
        node = create_test_node(energy=0.1)
        
        # Update 5 times
        for i in range(5):
            node.energy = float(i)
            buffer.mark_dirty(node)
        
        # Flush once
        count = buffer.flush()
        
        # Only 1 write (last state)
        assert count == 1
        assert len(written) == 1
        assert written[0].energy == 4.0
        assert buffer.writes_coalesced == 4  # 4 overwrites
    
    def test_swap_release_no_block(self):
        """
        mark_dirty() should NOT block while flush() is doing IO.
        
        This test simulates a 50ms DB hang and verifies mark_dirty completes in <10ms.
        """
        call_times = []
        
        def slow_write(nodes):
            # Simulate 50ms DB hang
            time.sleep(0.05)
        
        buffer = WriteBackBuffer(
            storage_write_fn=slow_write,
            key_func=lambda n: n.id,
            num_shards=16
        )
        
        # Add initial node
        node1 = create_test_node()
        buffer.mark_dirty(node1)
        
        # Start flush in background
        flush_thread = threading.Thread(target=buffer.flush)
        flush_thread.start()
        
        # Wait a bit for flush to start
        time.sleep(0.005)
        
        # Now try to mark_dirty while flush is in progress
        node2 = create_test_node()  # Different node, likely different shard
        
        start = time.perf_counter()
        buffer.mark_dirty(node2)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        flush_thread.join()
        
        # mark_dirty should complete in <10ms even if flush takes 50ms
        # (because IO is outside the lock)
        assert elapsed_ms < 10, f"mark_dirty took {elapsed_ms:.2f}ms, expected <10ms"
    
    def test_requeue_on_failure(self):
        """Failed writes should be requeued for retry."""
        fail_count = [0]
        
        def failing_write(nodes):
            fail_count[0] += 1
            if fail_count[0] == 1:
                raise Exception("Simulated DB failure")
        
        buffer = WriteBackBuffer(
            storage_write_fn=failing_write,
            key_func=lambda n: n.id,
            num_shards=1  # Force same shard
        )
        
        node = create_test_node()
        buffer.mark_dirty(node)
        
        # First flush fails
        buffer.flush()
        
        # Node should be requeued
        assert buffer.pending_count() == 1
        
        # Second flush should succeed
        buffer.flush()
        assert buffer.pending_count() == 0
        assert fail_count[0] == 2


class TestEdgeBuffer:
    
    def test_edge_keying(self):
        """Edges should be keyed by (source, target) tuple."""
        from rmm import Edge
        
        written = []
        
        def mock_write(edges):
            written.extend(edges)
        
        buffer = WriteBackBuffer(
            storage_write_fn=mock_write,
            key_func=lambda e: (e.source, e.target),
            num_shards=4
        )
        
        src = uuid.uuid4()
        tgt = uuid.uuid4()
        
        # Update same edge 3 times
        for i in range(3):
            edge = Edge(source=src, target=tgt, weight=0.1 * (i + 1))
            buffer.mark_dirty(edge)
        
        count = buffer.flush()
        
        # Only 1 edge written (last weight)
        assert count == 1
        assert len(written) == 1
        assert written[0].weight == pytest.approx(0.3)
