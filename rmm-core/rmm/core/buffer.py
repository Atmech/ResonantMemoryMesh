"""
RMM WriteBackBuffer - Async coalescing with Swap & Release pattern.

Key features:
- Generic key_func for Node/Edge support
- Sharded mutex (16 shards by default)
- DB IO outside lock to prevent contention
- Retry/requeue on failure for durability
"""
import logging
import threading
import uuid
from typing import Dict, List, Callable, TypeVar, Generic, Optional

logger = logging.getLogger(__name__)

T = TypeVar('T')
K = TypeVar('K')


class WriteBackBuffer(Generic[T, K]):
    """
    Generic async write-back buffer with Swap & Release pattern.
    
    Args:
        storage_write_fn: Function to call for batch writes
        key_func: Extracts unique key from item (e.g., node.id or (edge.source, edge.target))
        shard_func: Determines shard from key (default: hash % num_shards)
        num_shards: Number of lock shards (default: 16)
        flush_interval_ms: Background flush interval (default: 100ms)
        load_shed_threshold: When pending > threshold, aggressively coalesce (default: 5000)
    """
    
    def __init__(
        self,
        storage_write_fn: Callable[[List[T]], None],
        key_func: Callable[[T], K],
        num_shards: int = 16,
        flush_interval_ms: int = 100,
        load_shed_threshold: int = 5000,
    ):
        self.storage_write_fn = storage_write_fn
        self.key_func = key_func
        self.num_shards = num_shards
        self.flush_interval = flush_interval_ms / 1000.0
        self.load_shed_threshold = load_shed_threshold
        
        # Per-shard dirty buffers + locks
        self.shards: List[Dict[K, T]] = [{} for _ in range(num_shards)]
        self.locks: List[threading.Lock] = [threading.Lock() for _ in range(num_shards)]
        
        # Flush thread control
        self._running = False
        self._flush_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Metrics
        self.writes_coalesced = 0
        self.total_flushed = 0
        self.load_shed_events = 0
        
    def _get_shard(self, key: K) -> int:
        """Determine shard ID from key."""
        if isinstance(key, uuid.UUID):
            return key.int % self.num_shards
        elif isinstance(key, tuple):
            # For edges: hash of (source, target)
            return hash(key) % self.num_shards
        else:
            return hash(key) % self.num_shards
    
    def _check_load_shed(self) -> bool:
        """Check if pending count exceeds load shed threshold (fast, approximate)."""
        # Approximate count without locking all shards
        approx_count = sum(len(s) for s in self.shards)
        return approx_count > self.load_shed_threshold
    
    def mark_dirty(self, item: T) -> None:
        """
        Buffer an item update (coalesces automatically via Last-Write-Wins).
        Non-blocking under normal operation.
        
        Load shedding: If pending > threshold, triggers emergency flush.
        """
        key = self.key_func(item)
        shard_id = self._get_shard(key)
        
        with self.locks[shard_id]:
            if key in self.shards[shard_id]:
                self.writes_coalesced += 1
            self.shards[shard_id][key] = item
        
        # Load shedding: check if we're overloaded
        if self._check_load_shed():
            logger.warning(f"Load shed triggered: pending > {self.load_shed_threshold}")
            self.load_shed_events += 1
            # Trigger immediate flush in separate thread to avoid blocking
            threading.Thread(target=self.flush, daemon=True).start()
    
    def flush(self) -> int:
        """
        Flush all dirty items to storage using Swap & Release pattern.
        
        Returns: Number of items flushed.
        """
        total = 0
        
        for shard_id in range(self.num_shards):
            items_to_write: List[T] = []
            
            # 1. SWAP: Minimum lock duration - just swap data out
            with self.locks[shard_id]:
                if self.shards[shard_id]:
                    items_to_write = list(self.shards[shard_id].values())
                    self.shards[shard_id].clear()
            
            # 2. RELEASE: IO happens OUTSIDE the lock
            if items_to_write:
                try:
                    self.storage_write_fn(items_to_write)
                    total += len(items_to_write)
                except Exception as e:
                    # 3. DURABILITY: Requeue on failure
                    self._requeue_failed(shard_id, items_to_write)
                    logger.error(f"Flush shard {shard_id} failed: {e}")
        
        self.total_flushed += total
        return total
    
    def _requeue_failed(self, shard_id: int, items: List[T]) -> None:
        """Merge failed items back to shard (Last-Write-Wins respects newer writes)."""
        with self.locks[shard_id]:
            for item in items:
                key = self.key_func(item)
                # Only requeue if not superseded by newer write
                if key not in self.shards[shard_id]:
                    self.shards[shard_id][key] = item
    
    def start(self) -> None:
        """Start background flush thread."""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()
    
    def stop(self) -> None:
        """Stop background flush thread."""
        self._running = False
        self._stop_event.set()
        if self._flush_thread:
            self._flush_thread.join(timeout=2.0)
            self._flush_thread = None
    
    def _flush_loop(self) -> None:
        """Background flush loop."""
        while self._running:
            self._stop_event.wait(timeout=self.flush_interval)
            if self._running:
                try:
                    self.flush()
                except Exception as e:
                    logger.error(f"Background flush error: {e}")
    
    def pending_count(self) -> int:
        """Count of items waiting to be flushed."""
        total = 0
        for shard_id in range(self.num_shards):
            with self.locks[shard_id]:
                total += len(self.shards[shard_id])
        return total
