"""RMM Adapters - Storage backends"""
from rmm.adapters.base import BaseStorage
from rmm.adapters.memory import InMemoryStorage

__all__ = ["BaseStorage", "InMemoryStorage"]
