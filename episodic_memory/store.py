from __future__ import annotations

import json
import math
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Tuple, Optional

from .models import (
    EncodedExperience,
    EpisodicMemorySystem,
    Governance,
    IndexMap,
    IndexingStructures,
    IntegrationPlan,
    MemoryEntry,
    MemoryStamp,
    SemanticCluster,
    SystemConfiguration,
    SystemMetadata,
)
from .utils import load_system_from_path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_embed(text: str, dim: int) -> List[float]:
    """
    Deterministic, lightweight hashing-encoder over character n-grams.
    CPU-friendly and dependency-free; normalizes to unit length.
    """
    import hashlib

    vec = [0.0] * max(1, dim)
    if not text:
        return vec
    n = 3 if len(text) >= 3 else 1
    data = text.encode("utf-8", errors="ignore")
    # Iterate over n-grams; use stable sha256-based bucketing
    for i in range(0, max(1, len(data) - n + 1)):
        gram = data[i : i + n]
        h = hashlib.sha256(gram + b"\x13\x37").digest()
        idx = int.from_bytes(h[:4], "little", signed=False) % dim
        vec[idx] += 1.0
    # L2 normalize to allow cosine similarity
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


@dataclass
class RetrievalResult:
    memory_id: str
    score: float
    similarity: float
    importance: float
    raw_text: str


class MemoryStore:
    def __init__(self, system: EpisodicMemorySystem):
        self.system = system

    @staticmethod
    def load(path: str) -> "MemoryStore":
        data = load_system_from_path(path)
        system = EpisodicMemorySystem.from_dict(data)
        return MemoryStore(system)

    # --- Persistence ---
    def to_dict(self) -> dict:
        # Minimal round-trip serializer for current structure
        sm = self.system.system_metadata
        cfg = sm.configuration
        system_metadata = {
            "version": sm.version,
            "created_at": sm.created_at,
            "updated_at": sm.updated_at,
            "embedding_dimension": sm.embedding_dimension,
            "total_memories": sm.total_memories,
            "storage_path": sm.storage_path,
            "configuration": {
                "similarity_threshold": cfg.similarity_threshold,
                "max_retrieval_results": cfg.max_retrieval_results,
                "auto_clustering_enabled": cfg.auto_clustering_enabled,
                "temporal_decay_factor": cfg.temporal_decay_factor,
            },
        }

        memory_entries = {}
        for k, v in self.system.memory_entries.items():
            ee = v.encoded_experience
            ms = v.memory_stamp
            im = v.index_map
            ip = v.integration_plan
            memory_entries[k] = {
                "memory_stamp": {
                    "timestamp": ms.timestamp,
                    "event_id": ms.event_id,
                    "location": ms.location,
                    "source": ms.source,
                    "signature_hash": ms.signature_hash,
                    "session_id": ms.session_id,
                    "user_id": ms.user_id,
                },
                "encoded_experience": {
                    "raw_text": ee.raw_text,
                    "vector_embedding": ee.vector_embedding,
                    "reward_signal": ee.reward_signal,
                    "emotional_tone": ee.emotional_tone,
                    "context_tags": ee.context_tags,
                    "importance_score": ee.importance_score,
                    "associated_emotions": [
                        {"emotion": e.emotion, "intensity": e.intensity} for e in ee.associated_emotions
                    ],
                },
                "index_map": {
                    "semantic_cluster_id": im.semantic_cluster_id,
                    "time_index": im.time_index,
                    "graph_node_id": im.graph_node_id,
                    "related_nodes": im.related_nodes,
                    "hierarchical_path": im.hierarchical_path,
                    "access_frequency": im.access_frequency,
                    "last_accessed": im.last_accessed,
                },
                "integration_plan": {
                    "augmentation_target": ip.augmentation_target,
                    "confidence_score": ip.confidence_score,
                    "integration_notes": ip.integration_notes,
                    "priority_weight": ip.priority_weight,
                    "staleness_factor": ip.staleness_factor,
                    "context_relevance": ip.context_relevance,
                },
            }

        idx = self.system.indexing_structures
        indexing_structures = {
            "semantic_clusters": {
                cid: {
                    "cluster_id": sc.cluster_id,
                    "centroid_embedding": sc.centroid_embedding,
                    "member_count": sc.member_count,
                    "memory_ids": sc.memory_ids,
                    "creation_timestamp": sc.creation_timestamp,
                    "last_updated": sc.last_updated,
                    "cluster_quality_score": sc.cluster_quality_score,
                }
                for cid, sc in idx.semantic_clusters.items()
            },
            "temporal_index": idx.temporal_index,
            "graph_connections": {
                nid: {
                    "node_id": gn.node_id,
                    "connections": [
                        {
                            "target_node_id": c.target_node_id,
                            "connection_strength": c.connection_strength,
                            "connection_type": c.connection_type,
                            "created_at": c.created_at,
                        }
                        for c in gn.connections
                    ],
                    "centrality_score": gn.centrality_score,
                    "clustering_coefficient": gn.clustering_coefficient,
                }
                for nid, gn in idx.graph_connections.items()
            },
        }

        integration_specifications = {
            "llm_context_format": self.system.integration_specifications.llm_context_format.__dict__,
            "planner_input_format": self.system.integration_specifications.planner_input_format.__dict__,
            "rl_replay_format": self.system.integration_specifications.rl_replay_format.__dict__,
        }

        return {
            "system_metadata": system_metadata,
            "memory_entries": memory_entries,
            "indexing_structures": indexing_structures,
            "integration_specifications": integration_specifications,
            **({"governance": {
                "provenance_chain": [
                    {"step": p.step, "actor": p.actor, "time": p.time, "hash": p.hash}
                    for p in (self.system.governance.provenance_chain if self.system.governance else [])
                ],
                **({
                    "retention_policy": {
                        "class": self.system.governance.retention_policy.class_,
                        "review_after": self.system.governance.retention_policy.review_after,
                        "decay": self.system.governance.retention_policy.decay,
                    }
                } if (self.system.governance and self.system.governance.retention_policy) else {}),
                **({
                    "access_control": {
                        "read": self.system.governance.access_control.read,
                        "write": self.system.governance.access_control.write,
                    }
                } if (self.system.governance and self.system.governance.access_control) else {}),
            }} if self.system.governance else {}),
        }

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    # --- Mutations ---
    def add_memory(
        self,
        raw_text: str,
        context_tags: List[str],
        importance_score: float = 0.5,
        reward_signal: float = 0.0,
        emotional_tone: str = "neutral",
        vector_embedding: Optional[List[float]] = None,
        *,
        embedder: Optional[object] = None,
        embed_dim: Optional[int] = None,
        location: str = "",
        source: str = "api",
        session_id: Optional[str] = None,
        user_id: str = "",
    ) -> str:
        sm = self.system.system_metadata
        dim = embed_dim or sm.embedding_dimension
        if vector_embedding is not None:
            vec = vector_embedding
        else:
            if embedder is not None:
                # duck-typed embedder
                vec = embedder.embed(raw_text, dim)
            else:
                vec = _hash_embed(raw_text, dim)
        now = _utc_now_iso()
        event_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())

        entry = MemoryEntry(
            memory_stamp=MemoryStamp(
                timestamp=now,
                event_id=event_id,
                location=location,
                source=source,
                signature_hash=event_id.replace("-", "")[:16],
                session_id=session_id,
                user_id=user_id,
            ),
            encoded_experience=EncodedExperience(
                raw_text=raw_text,
                vector_embedding=vec,
                reward_signal=reward_signal,
                emotional_tone=emotional_tone,
                context_tags=context_tags,
                importance_score=importance_score,
                associated_emotions=[],
            ),
            index_map=IndexMap(
                semantic_cluster_id=self._assign_cluster(vec),
                time_index=now[:10],
                graph_node_id=str(uuid.uuid4()),
                related_nodes=[],
                hierarchical_path=list(context_tags[:3]),
                access_frequency=0,
                last_accessed=now,
            ),
            integration_plan=IntegrationPlan(
                augmentation_target="LLM_context",
                confidence_score=0.0,
                integration_notes="",
                priority_weight=importance_score,
                staleness_factor=0.0,
                context_relevance=0.0,
            ),
        )

        self.system.memory_entries[event_id] = entry
        sm.total_memories = len(self.system.memory_entries)
        sm.updated_at = now
        self._update_indexes_for_new_entry(event_id, entry)
        return event_id

    # --- Maintenance ---
    def rebuild_indexes(self) -> None:
        """Rebuild semantic clusters and temporal index from scratch."""
        # Reset
        self.system.indexing_structures.semantic_clusters = {}
        self.system.indexing_structures.temporal_index = {}
        # Re-add all
        for mem_id, entry in self.system.memory_entries.items():
            # Assign cluster for each based on current centroids
            cid = self._assign_cluster(entry.encoded_experience.vector_embedding)
            entry.index_map.semantic_cluster_id = cid
            entry.index_map.time_index = (entry.index_map.time_index or entry.memory_stamp.timestamp[:10])
            if not entry.index_map.last_accessed:
                entry.index_map.last_accessed = entry.memory_stamp.timestamp
            self._update_indexes_for_new_entry(mem_id, entry)

    def reembed_all(self, embedder: object, dim: Optional[int] = None) -> None:
        sm = self.system.system_metadata
        dim = dim or sm.embedding_dimension
        for entry in self.system.memory_entries.values():
            entry.encoded_experience.vector_embedding = embedder.embed(entry.encoded_experience.raw_text, dim)
        sm.embedding_dimension = dim
        sm.updated_at = _utc_now_iso()
        self.rebuild_indexes()

    # --- Retrieval ---
    def search(self, query_text: str, top_k: int | None = None, *, embedder: Optional[object] = None) -> List[RetrievalResult]:
        sm = self.system.system_metadata
        cfg = sm.configuration
        dim = sm.embedding_dimension
        # Prefer caller-provided embedder (duck-typed with .embed), else built-in hash
        if embedder is not None:
            try:
                q = embedder.embed(query_text, dim)  # type: ignore[attr-defined]
            except Exception:
                q = _hash_embed(query_text, dim)
        else:
            q = _hash_embed(query_text, dim)
        top_k = top_k or cfg.max_retrieval_results

        results: List[Tuple[str, float, float, float, str]] = []
        for mem_id, entry in self.system.memory_entries.items():
            ee = entry.encoded_experience
            sim = _cosine(q, ee.vector_embedding)
            if sim < cfg.similarity_threshold:
                continue
            recency = self._recency_weight(entry.index_map.last_accessed, cfg.temporal_decay_factor)
            importance = ee.importance_score
            score = sim * 0.7 + recency * 0.2 + importance * 0.1
            results.append((mem_id, score, sim, importance, ee.raw_text))

        results.sort(key=lambda x: x[1], reverse=True)
        out = [
            RetrievalResult(memory_id=i, score=s, similarity=sim, importance=imp, raw_text=txt)
            for i, s, sim, imp, txt in results[:top_k]
        ]
        # Update access frequency for returned items
        now = _utc_now_iso()
        for r in out:
            entry = self.system.memory_entries[r.memory_id]
            entry.index_map.access_frequency += 1
            entry.index_map.last_accessed = now
        return out

    # --- Helpers ---
    def _recency_weight(self, last_accessed_iso: str, decay: float) -> float:
        try:
            last = datetime.strptime(last_accessed_iso.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z")
        except Exception:
            return 0.5
        now = datetime.now(timezone.utc)
        delta_sec = max(0.0, (now - last).total_seconds())
        # half-life style decay per day
        days = delta_sec / 86400.0
        return math.pow(decay, days)

    def _assign_cluster(self, vec: List[float]) -> str:
        # Nearest centroid, create one if none exists
        idx = self.system.indexing_structures
        if not idx.semantic_clusters:
            cid = "cluster_0"
            idx.semantic_clusters[cid] = SemanticCluster(
                cluster_id=cid,
                centroid_embedding=vec[:],
                member_count=0,
                memory_ids=[],
                creation_timestamp=_utc_now_iso(),
                last_updated=_utc_now_iso(),
                cluster_quality_score=1.0,
            )
            return cid

        # Find closest
        best: Tuple[str, float] | None = None
        for cid, c in idx.semantic_clusters.items():
            sim = _cosine(vec, c.centroid_embedding)
            if best is None or sim > best[1]:
                best = (cid, sim)
        assert best is not None
        return best[0]

    def _update_indexes_for_new_entry(self, mem_id: str, entry: MemoryEntry) -> None:
        idx = self.system.indexing_structures
        # Update cluster centroid
        cid = entry.index_map.semantic_cluster_id
        c = idx.semantic_clusters.get(cid)
        if c is None:
            c = SemanticCluster(
                cluster_id=cid,
                centroid_embedding=entry.encoded_experience.vector_embedding[:],
                member_count=0,
                memory_ids=[],
                creation_timestamp=_utc_now_iso(),
                last_updated=_utc_now_iso(),
                cluster_quality_score=1.0,
            )
            idx.semantic_clusters[cid] = c

        # Online centroid update
        m = c.member_count
        old = c.centroid_embedding
        new = entry.encoded_experience.vector_embedding
        if not old:
            c.centroid_embedding = new[:]
        else:
            c.centroid_embedding = [((old[i] * m) + new[i]) / (m + 1) for i in range(len(new))]
        c.member_count += 1
        c.memory_ids.append(mem_id)
        c.last_updated = _utc_now_iso()

        # Temporal index
        day = entry.index_map.time_index
        ti = idx.temporal_index.setdefault(day, {"date": day, "memory_ids": [], "event_density": 0, "significance_score": 0.0})
        ti["memory_ids"].append(mem_id)
        ti["event_density"] = int(ti.get("event_density", 0)) + 1
