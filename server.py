from __future__ import annotations

import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
import threading
from pydantic import BaseModel

from episodic_memory import MemoryStore, load_system_from_path, __version__ as PKG_VERSION
from episodic_memory.models import EpisodicMemorySystem
from episodic_memory.schema import load_schema, validate_instance
from episodic_memory.embeddings import get_embedder, CachedEmbedder


app = FastAPI(title="Episodic Memory Service", version=PKG_VERSION)
_EMBED_CONCURRENCY = int(os.getenv("EMBED_CONCURRENCY", "4"))
_EMBED_SEM = threading.Semaphore(_EMBED_CONCURRENCY)


class ValidateRequest(BaseModel):
    data: Optional[dict] = None
    path: Optional[str] = None
    schema: bool = False


class SearchRequest(BaseModel):
    path: str
    query: str
    top_k: int = 5
    threshold: Optional[float] = None


class AddRequest(BaseModel):
    path: str
    text: str
    tags: List[str] = []
    importance: float = 0.5
    reward: float = 0.0
    tone: str = "neutral"
    embedder: Optional[str] = None
    openai_model: Optional[str] = None
    embed_dim: Optional[int] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/validate")
def validate(req: ValidateRequest):
    if not req.data and not req.path:
        raise HTTPException(status_code=400, detail="Provide either data or path")
    data = req.data or load_system_from_path(req.path)  # type: ignore
    ok, msg = True, None
    if req.schema:
        schema = load_schema(None)
        ok, msg = validate_instance(data, schema)
    if not ok:
        raise HTTPException(status_code=422, detail=msg or "Schema validation failed")
    store = MemoryStore(EpisodicMemorySystem.from_dict(data))  # type: ignore
    sm = store.system.system_metadata
    return {"total_memories": sm.total_memories, "embedding_dimension": sm.embedding_dimension}


@app.post("/search")
def search(req: SearchRequest):
    store = MemoryStore.load(req.path)
    if req.threshold is not None:
        store.system.system_metadata.configuration.similarity_threshold = float(req.threshold)
    results = store.search(req.query, top_k=req.top_k)
    return [r.__dict__ for r in results]


@app.post("/add")
def add(req: AddRequest):
    store = MemoryStore.load(req.path)
    embedder = None
    if req.embedder:
        base = get_embedder(req.embedder, model=req.openai_model)
        embedder = CachedEmbedder(base, backend_name=req.embedder, model_id=req.openai_model)
    # Throttle embedding to reduce CPU spikes
    with _EMBED_SEM:
        mem_id = store.add_memory(
            raw_text=req.text,
            context_tags=req.tags,
            importance_score=req.importance,
            reward_signal=req.reward,
            emotional_tone=req.tone,
            embedder=embedder,
            embed_dim=req.embed_dim,
            source="api",
            user_id="api",
        )
    store.save(req.path)
    return {"memory_id": mem_id}
