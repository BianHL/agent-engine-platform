"""Semantic cache for model responses using content hashing."""
import hashlib
import json
import time
from typing import Any, Callable, Optional

import numpy as np


class SemanticCache:
    """Cache model responses by message content hash."""

    def __init__(self, ttl: int = 3600):
        self._store: dict[str, dict] = {}  # key -> {"response": ..., "timestamp": ..., "tenant_id": ...}
        self._ttl = ttl

    async def get(self, messages: list[dict], tenant_id: str = None) -> Optional[dict]:
        key = self._make_key(messages)
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() - entry["timestamp"] > self._ttl:
            del self._store[key]
            return None
        if tenant_id and entry.get("tenant_id") != tenant_id:
            return None
        return entry["response"]

    async def set(self, messages: list[dict], response: dict, tenant_id: str = None):
        key = self._make_key(messages)
        self._store[key] = {
            "response": response,
            "timestamp": time.time(),
            "tenant_id": tenant_id,
        }

    async def clear(self, tenant_id: str = None):
        if tenant_id:
            keys_to_del = [k for k, v in self._store.items() if v.get("tenant_id") == tenant_id]
            for k in keys_to_del:
                del self._store[k]
        else:
            self._store.clear()

    def _make_key(self, messages: list[dict]) -> str:
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = m.get("content", "")
                break
        return hashlib.sha256(last_user.encode()).hexdigest()[:32]


class VectorSemanticCache:
    """Semantic cache using embedding similarity."""

    def __init__(self, threshold: float = 0.92, ttl: int = 3600):
        self._threshold = threshold
        self._ttl = ttl
        self._entries: list[dict] = []
        self._embedder: Optional[Callable] = None

    def set_embedder(self, embedder: Callable):
        """Set embedding function: async def embed(text) -> list[float]"""
        self._embedder = embedder

    async def get(self, messages: list[dict], tenant_id: str = None) -> Optional[dict]:
        query_text = self._extract_query(messages)
        if not query_text or not self._embedder:
            return None

        query_vec = np.array(await self._embedder(query_text))
        if np.linalg.norm(query_vec) == 0:
            return None

        now = time.time()
        best_match = None
        best_sim = 0.0

        for entry in self._entries:
            if now - entry["timestamp"] > self._ttl:
                continue
            if tenant_id and entry.get("tenant_id") != tenant_id:
                continue
            sim = self._cosine_sim(query_vec, entry["vector"])
            if sim > best_sim:
                best_sim = sim
                best_match = entry

        if best_match and best_sim >= self._threshold:
            return best_match["response"]
        return None

    async def set(self, messages: list[dict], response: dict, tenant_id: str = None):
        query_text = self._extract_query(messages)
        if not query_text or not self._embedder:
            return

        vec = np.array(await self._embedder(query_text))
        self._entries.append({
            "vector": vec,
            "response": response,
            "timestamp": time.time(),
            "tenant_id": tenant_id,
            "text": query_text,
        })

        if len(self._entries) > 1000:
            self._entries = self._entries[-500:]

    async def clear(self, tenant_id: str = None):
        if tenant_id:
            self._entries = [e for e in self._entries if e.get("tenant_id") != tenant_id]
        else:
            self._entries.clear()

    def _extract_query(self, messages: list[dict]) -> str:
        for m in reversed(messages):
            if m.get("role") == "user":
                return m.get("content", "")
        return ""

    @staticmethod
    def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
