"""
TelePort2PI — Memory System
Handles explicit memory storage, embedding-based retrieval, and memory management.
"""

import json
import logging
import math
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────
MAX_MEMORIES_PER_USER = 50
TOP_K_MEMORIES = 3
SIMILARITY_THRESHOLD = 0.4          # below this score, memory is ignored
MEMORY_TRIGGER_PHRASES = (
    "remember ",
    "save this",
    "note that ",
    "note: ",
    "don't forget ",
    "keep in mind ",
)
EMBED_MODEL = "nomic-embed-text"    # pulled separately: ollama pull nomic-embed-text


class MemoryManager:
    """
    Per-user long-term memory with embedding-based semantic retrieval.

    Storage layout (data/memory.json):
    {
        "<user_id>": {
            "memories": [
                {
                    "text": "...",
                    "embedding": [...],   # null if embed model unavailable
                    "created_at": 1234567890.0
                }
            ]
        }
    }
    """

    def __init__(self, data_path: str, ollama_base_url: str):
        self.data_path = data_path
        self.ollama_base_url = ollama_base_url.rstrip("/")
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        self._store: dict = self._load()

    # ── Public API ───────────────────────────────────────────

    def detect_memory_intent(self, text: str) -> Optional[str]:
        """
        Check if the message is asking to store something.
        Returns the text to remember (stripped of trigger phrase), or None.
        """
        lower = text.lower()
        for phrase in MEMORY_TRIGGER_PHRASES:
            if lower.startswith(phrase):
                memory_text = text[len(phrase):].strip()
                if memory_text:
                    return memory_text
        return None

    def add_memory(self, user_id: int, text: str) -> bool:
        """
        Store a new memory for the user. Returns True on success.
        Embeddings are generated if the embed model is available; otherwise stored as None.
        """
        uid = str(user_id)
        if uid not in self._store:
            self._store[uid] = {"memories": []}

        memories = self._store[uid]["memories"]

        # Deduplicate — skip if very similar text already stored
        if any(m["text"].lower() == text.lower() for m in memories):
            logger.debug("Memory already exists for user %s: %s", uid, text[:60])
            return False

        # Enforce per-user limit (drop oldest)
        if len(memories) >= MAX_MEMORIES_PER_USER:
            self._store[uid]["memories"] = memories[-(MAX_MEMORIES_PER_USER - 1):]

        embedding = self._get_embedding(text)
        self._store[uid]["memories"].append({
            "text": text,
            "embedding": embedding,
            "created_at": time.time(),
        })
        self._save()
        logger.info("Stored memory for user %s: %s", uid, text[:60])
        return True

    def retrieve_relevant(self, user_id: int, query: str) -> list[str]:
        """
        Return up to TOP_K_MEMORIES memory texts most relevant to the query.
        Falls back to recency-based retrieval if embeddings unavailable.
        """
        uid = str(user_id)
        memories = self._store.get(uid, {}).get("memories", [])
        if not memories:
            return []

        query_embedding = self._get_embedding(query)

        if query_embedding is None:
            # No embed model — return last TOP_K recent memories
            return [m["text"] for m in memories[-TOP_K_MEMORIES:]]

        scored = []
        for mem in memories:
            mem_emb = mem.get("embedding")
            if mem_emb:
                score = _cosine_similarity(query_embedding, mem_emb)
                if score >= SIMILARITY_THRESHOLD:
                    scored.append((score, mem["text"]))
            else:
                # Memory was stored without embedding — re-embed now
                new_emb = self._get_embedding(mem["text"])
                if new_emb:
                    mem["embedding"] = new_emb
                    score = _cosine_similarity(query_embedding, new_emb)
                    if score >= SIMILARITY_THRESHOLD:
                        scored.append((score, mem["text"]))

        self._save()  # persist any newly computed embeddings
        scored.sort(reverse=True, key=lambda x: x[0])
        return [text for _, text in scored[:TOP_K_MEMORIES]]

    def list_memories(self, user_id: int) -> list[str]:
        """Return all stored memory texts for a user (no embeddings)."""
        uid = str(user_id)
        return [m["text"] for m in self._store.get(uid, {}).get("memories", [])]

    def delete_memory(self, user_id: int, fragment: str) -> bool:
        """
        Delete a memory whose text contains `fragment` (case-insensitive).
        Returns True if something was deleted.
        """
        uid = str(user_id)
        memories = self._store.get(uid, {}).get("memories", [])
        before = len(memories)
        self._store[uid]["memories"] = [
            m for m in memories if fragment.lower() not in m["text"].lower()
        ]
        if len(self._store[uid]["memories"]) < before:
            self._save()
            return True
        return False

    def clear_memories(self, user_id: int) -> int:
        """Wipe all memories for a user. Returns count deleted."""
        uid = str(user_id)
        count = len(self._store.get(uid, {}).get("memories", []))
        self._store[uid] = {"memories": []}
        self._save()
        return count

    # ── Prompt Helper ────────────────────────────────────────

    def build_memory_context(self, user_id: int, query: str) -> str:
        """
        Return a formatted memory block ready for prompt injection,
        or an empty string if no relevant memories found.
        """
        relevant = self.retrieve_relevant(user_id, query)
        if not relevant:
            return ""
        lines = "\n".join(f"- {m}" for m in relevant)
        return f"Relevant context about the user:\n{lines}\n"

    # ── Private ──────────────────────────────────────────────

    def _get_embedding(self, text: str) -> Optional[list[float]]:
        """Call Ollama embed endpoint. Returns None if unavailable."""
        try:
            import requests
            resp = requests.post(
                f"{self.ollama_base_url}/api/embed",
                json={"model": EMBED_MODEL, "input": text},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                # Ollama returns {"embeddings": [[...]]} for /api/embed
                embeddings = data.get("embeddings") or data.get("embedding")
                if embeddings:
                    return embeddings[0] if isinstance(embeddings[0], list) else embeddings
        except Exception as e:
            logger.debug("Embedding unavailable (%s) — falling back to recency", e)
        return None

    def _load(self) -> dict:
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load memory store: %s — starting fresh", e)
        return {}

    def _save(self) -> None:
        try:
            with open(self.data_path, "w") as f:
                json.dump(self._store, f, indent=2)
        except OSError as e:
            logger.error("Failed to save memory store: %s", e)


# ── Math Helper ──────────────────────────────────────────────

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors (pure Python)."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)