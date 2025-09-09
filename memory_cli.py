#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from glob import glob
import json
import sys
from typing import Any

from episodic_memory import MemoryStore, load_system_from_path
from episodic_memory.models import EpisodicMemorySystem
from episodic_memory.schema import load_schema, validate_instance
from episodic_memory.embeddings import get_embedder, CachedEmbedder
from episodic_memory.faiss_index import FaissIndexManager, _MissingFaiss
from typing import Optional

# optional progress reporting
try:
    from tqdm import tqdm  # type: ignore
except Exception:  # pragma: no cover
    tqdm = None
import logging
logger = logging.getLogger(__name__)


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        data = load_system_from_path(args.path)
        system = EpisodicMemorySystem.from_dict(data)
    except Exception as e:
        print(f"Invalid file: {e}", file=sys.stderr)
        return 2
    ok = True
    msg = None
    if args.schema:
        schema = load_schema(args.schema if args.schema != "auto" else None)
        ok, msg = validate_instance(data, schema)
    print("OK: Parsed episodic memory system")
    print(json.dumps({
        "total_memories": system.system_metadata.total_memories,
        "embedding_dimension": system.system_metadata.embedding_dimension,
    }, indent=2))
    if args.schema:
        if ok:
            print("Schema validation: OK")
        else:
            print("Schema validation: FAILED")
            print(msg or "Unknown schema error", file=sys.stderr)
            return 3
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    store = MemoryStore.load(args.path)
    if args.threshold is not None:
        store.system.system_metadata.configuration.similarity_threshold = float(args.threshold)
    # Optional embedder for query parity with stored vectors
    embedder = None
    if getattr(args, "embedder", None):
        base = get_embedder(args.embedder, model=args.openai_model)
        embedder = CachedEmbedder(base, backend_name=args.embedder, model_id=args.openai_model)
    results = store.search(args.query, top_k=args.top_k, embedder=embedder)
    if not results:
        print("No results above threshold.")
        return 0
    for r in results:
        print(f"- id={r.memory_id} score={r.score:.3f} sim={r.similarity:.3f} importance={r.importance:.2f}")
        print(f"  text: {r.raw_text}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    store = MemoryStore.load(args.path)
    embedder = None
    if args.embedder:
        base = get_embedder(args.embedder, model=args.openai_model)
        embedder = CachedEmbedder(base, backend_name=args.embedder, model_id=args.openai_model)
    mem_id = store.add_memory(
        raw_text=args.text,
        context_tags=args.tags,
        importance_score=args.importance,
        reward_signal=args.reward,
        emotional_tone=args.tone,
        embedder=embedder,
        embed_dim=args.embed_dim,
        location=args.location,
        source="cli",
        user_id=args.user_id,
    )
    store.save(args.path)
    print(f"Added memory: {mem_id}")
    return 0


def cmd_schema_validate(args: argparse.Namespace) -> int:
    try:
        data = load_system_from_path(args.path)
        schema = load_schema(args.schema if args.schema != "auto" else None)
        ok, msg = validate_instance(data, schema)
        if ok:
            print("Schema validation: OK")
            return 0
        print("Schema validation: FAILED")
        print(msg or "Unknown error", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 2


def _write_output(data: dict, in_path: str, out_path: str | None, in_place: bool) -> str:
    path = in_path if in_place and not out_path else (out_path or in_path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def cmd_fix(args: argparse.Namespace) -> int:
    # Load messy file -> last object, coerce minimal consistency, optional re-embed and rebuild indexes
    data = load_system_from_path(args.path)
    system = EpisodicMemorySystem.from_dict(data)
    store = MemoryStore(system)

    # Ensure counts
    system.system_metadata.total_memories = len(system.memory_entries)

    # Embedding dimension reconciliation
    dims = {len(v.encoded_experience.vector_embedding) for v in system.memory_entries.values() if v.encoded_experience.vector_embedding}
    target_dim = args.embed_dim or (dims.pop() if len(dims) == 1 else (max(dims) if dims else system.system_metadata.embedding_dimension))
    if args.reembed or len(dims) > 0 or system.system_metadata.embedding_dimension != target_dim:
        base = get_embedder(args.embedder, model=args.openai_model) if args.embedder else get_embedder("hash")
        embedder = CachedEmbedder(base, backend_name=args.embedder or "hash", model_id=args.openai_model)
        store.reembed_all(embedder, dim=target_dim)
    else:
        # still align metadata dim
        system.system_metadata.embedding_dimension = target_dim

    # Fill missing last_accessed/time_index
    for entry in system.memory_entries.values():
        if not entry.index_map.last_accessed:
            entry.index_map.last_accessed = entry.memory_stamp.timestamp
        if not entry.index_map.time_index:
            entry.index_map.time_index = entry.memory_stamp.timestamp[:10]

    # Rebuild indexes for consistency
    store.rebuild_indexes()

    # Optionally validate against schema
    out_dict = store.to_dict()
    if args.schema:
        schema = load_schema(args.schema if args.schema != "auto" else None)
        ok, msg = validate_instance(out_dict, schema)
        if not ok:
            print("Warning: Schema validation failed post-fix:")
            print(msg or "Unknown schema error", file=sys.stderr)

    # Write out
    written = _write_output(out_dict, args.path, args.output, args.in_place)
    print(f"Wrote fixed file to: {written}")
    return 0


def cmd_index_build(args: argparse.Namespace) -> int:
    try:
        # Resolve data sources
        data_files: list[str] = []
        if args.data:
            if os.path.isdir(args.data):
                data_files = [p for p in glob(os.path.join(args.data, "**", "*.json"), recursive=True)]
            else:
                data_files = [args.data]
        elif args.path:
            data_files = [args.path]
        else:
            print("Provide either a positional <path> or --data (file or directory)", file=sys.stderr)
            return 2

        if not data_files:
            print("No JSON files found to index", file=sys.stderr)
            return 2

        out_index = args.output or args.index
        if not out_index:
            print("Provide an output index path via positional <index> or --output", file=sys.stderr)
            return 2

        # Initialize index manager from first file's dimension (EMS or generic JSON)
        def _detect_dim(fp: str) -> int:
            try:
                st = MemoryStore.load(fp)
                return int(st.system.system_metadata.embedding_dimension)
            except Exception:
                pass
            try:
                with open(fp, "r", encoding="utf-8") as fh:
                    d = json.load(fh)
                if isinstance(d, list):
                    for e in d:
                        if isinstance(e, dict):
                            vec = e.get("vector") or e.get("embedding")
                            if isinstance(vec, list) and vec:
                                return int(len(vec))
                if isinstance(d, dict):
                    if "memories" in d and isinstance(d["memories"], list):
                        for e in d["memories"]:
                            if isinstance(e, dict):
                                vec = e.get("vector") or e.get("embedding")
                                if isinstance(vec, list) and vec:
                                    return int(len(vec))
                    vec = d.get("vector") or d.get("embedding")
                    if isinstance(vec, list) and vec:
                        return int(len(vec))
            except Exception:
                pass
            raise RuntimeError(f"Unable to detect embedding dimension from {fp}")

        dim0 = _detect_dim(data_files[0])
        mgr = FaissIndexManager(dim0)
        mgr.meta_map = {}

        # Add vectors from each file, batching adds to smooth CPU
        batch_ids: list[str] = []
        batch_vecs: list[list[float]] = []
        dim = mgr.dim
        iterator = tqdm(data_files, desc="Indexing files") if tqdm else data_files
        for fp in iterator:
            # Try EMS first
            handled = False
            try:
                store = MemoryStore.load(fp)
                for mem_id, entry in store.system.memory_entries.items():
                    vec = entry.encoded_experience.vector_embedding
                    if not vec or len(vec) != dim:
                        continue
                    comp_id = f"{os.path.basename(fp)}::{mem_id}"
                    batch_ids.append(comp_id)
                    batch_vecs.append([float(x) for x in vec])
                    # record meta
                    try:
                        snippet = entry.encoded_experience.raw_text[:160]
                    except Exception:
                        snippet = ""
                    mgr.meta_map[comp_id] = {"source": fp, "snippet": snippet}
                    if len(batch_ids) >= args.batch_size:
                        mgr.add_vectors(batch_ids, batch_vecs, batch_size=args.batch_size, sleep_ms=args.sleep_ms)
                        batch_ids.clear()
                        batch_vecs.clear()
                handled = True
            except Exception:
                handled = False

            if not handled:
                # Generic JSON fallback
                try:
                    with open(fp, "r", encoding="utf-8") as fh:
                        d = json.load(fh)
                except Exception:
                    continue
                entries = []
                if isinstance(d, list):
                    entries = d
                elif isinstance(d, dict) and "memories" in d and isinstance(d["memories"], list):
                    entries = d["memories"]
                elif isinstance(d, dict):
                    entries = [d]

                for e in entries:
                    if not isinstance(e, dict):
                        continue
                    vec = e.get("vector") or e.get("embedding")
                    if not (isinstance(vec, list) and len(vec) == dim):
                        continue
                    mem_id = str(e.get("id") or e.get("memory_id") or len(mgr.ids))
                    comp_id = f"{os.path.basename(fp)}::{mem_id}"
                    batch_ids.append(comp_id)
                    batch_vecs.append([float(x) for x in vec])
                    snippet = e.get("snippet") or e.get("text") or ""
                    mgr.meta_map[comp_id] = {"source": fp, "snippet": snippet}
                    if len(batch_ids) >= args.batch_size:
                        mgr.add_vectors(batch_ids, batch_vecs, batch_size=args.batch_size, sleep_ms=args.sleep_ms)
                        batch_ids.clear()
                        batch_vecs.clear()
        if batch_ids:
            mgr.add_vectors(batch_ids, batch_vecs, batch_size=args.batch_size, sleep_ms=args.sleep_ms)

        # Ensure parent directory exists for index output
        out_dir = os.path.dirname(out_index or "")
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        mgr.save(out_index)
        print(f"Index built and saved to: {out_index}")
        return 0
    except _MissingFaiss as e:
        print(str(e), file=sys.stderr)
        return 2


# Backward/programmable wrappers for tests and integrations
def index_build(args: argparse.Namespace) -> int:
    """Wrapper alias to build index programmatically (matches test usage)."""
    return cmd_index_build(args)


def index_search_cli(args: argparse.Namespace) -> int:
    """Programmatic CLI-like search that prints JSON results.

    Delegates to cmd_index_search with sensible defaults.
    """
    # Ensure defaults expected by cmd_index_search
    for k, v in {
        "top_k": 5,
        "json": True,
        "embedder": None,
        "openai_model": None,
        "path": getattr(args, "path", None),
        "data": getattr(args, "data", None),
        "persist_meta": getattr(args, "persist_meta", False),
        "max_scan": getattr(args, "max_scan", 2000),
        "min_score": getattr(args, "min_score", None),
        "max_distance": getattr(args, "max_distance", None),
    }.items():
        if not hasattr(args, k) or getattr(args, k) is None:
            setattr(args, k, v)
    return cmd_index_search(args)


def cmd_index_search(args: argparse.Namespace) -> int:
    try:
        mgr = FaissIndexManager.load(args.index)
    except _MissingFaiss as e:
        print(str(e), file=sys.stderr)
        return 2
    # Optionally load meta mapping override from --data (file or directory)
    if getattr(args, "data", None):
        dp = args.data
        if os.path.isfile(dp) and dp.endswith(".json"):
            try:
                with open(dp, "r", encoding="utf-8") as mfh:
                    mm = json.load(mfh)
                    if isinstance(mm, dict) and "map" in mm:
                        mgr.meta_map = mm.get("map", {})
                    elif isinstance(mm, dict):
                        mgr.meta_map = mm
            except Exception:
                pass
        elif os.path.isdir(dp):
            meta_guess = args.index + ".meta.json"
            if os.path.exists(meta_guess):
                try:
                    with open(meta_guess, "r", encoding="utf-8") as mfh:
                        mm = json.load(mfh)
                        if isinstance(mm, dict) and "map" in mm:
                            mgr.meta_map = mm.get("map", {})
                except Exception:
                    pass
    # Build embedder and compute query vector
    store = None
    if getattr(args, "path", None):
        try:
            store = MemoryStore.load(args.path)
        except Exception:
            store = None
    base = get_embedder(args.embedder, model=args.openai_model) if args.embedder else get_embedder("hash")
    embedder = CachedEmbedder(base, backend_name=args.embedder or "hash", model_id=args.openai_model)
    # Use index dimension to avoid mismatches
    dim = mgr.dim if hasattr(mgr, "dim") else (store.system.system_metadata.embedding_dimension if store else 0)
    qv = embedder.embed(args.query, dim)
    hits = mgr.search(qv, top_k=args.top_k)
    # If max-distance is provided but using IP index, warn (option is ignored)
    if getattr(args, "max_distance", None) is not None:
        try:
            print("Note: --max-distance is ignored for IP indexes (IndexFlatIP).", file=sys.stderr)
        except Exception:
            pass
    # Threshold filters (assumes IP metric; L2 not used in IndexFlatIP)
    if getattr(args, "min_score", None) is not None:
        try:
            thr = float(args.min_score)
            hits = [(mid, sc) for (mid, sc) in hits if sc >= thr]
        except Exception:
            pass

    # Helper: attempt directory-based snippet fallback if meta missing
    def _dir_snippet(mid: str) -> tuple[str, str]:
        root = getattr(args, "data", None)
        if not root or not os.path.isdir(root):
            return "", ""
        if "::" not in mid:
            return "", ""
        base, mem_id = mid.split("::", 1)
        # Build a mapping from basename -> full path (bounded by max_scan)
        max_scan = max(0, int(getattr(args, "max_scan", 0) or 0))
        scanned = 0
        found_path: Optional[str] = None
        for dirpath, _dirnames, filenames in os.walk(root):
            for fname in filenames:
                if fname.lower().endswith(".json"):
                    scanned += 1
                    if fname == base:
                        found_path = os.path.join(dirpath, fname)
                        break
                    if max_scan and scanned >= max_scan:
                        break
            if found_path or (max_scan and scanned >= max_scan):
                break
        if not found_path:
            return "", ""
        try:
            with open(found_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return "", ""
        # Try EMS structure first
        try:
            obj = load_system_from_path(found_path)
            mem = obj.get("memory_entries", {}).get(mem_id)
            if mem:
                raw = (
                    mem.get("encoded_experience", {}).get("raw_text")
                    or mem.get("snippet")
                    or ""
                )
                sn = (raw[:120] + "...") if raw and len(raw) > 120 else (raw or "")
                return sn, found_path
        except Exception:
            pass
        # Fallback: generic list format
        try:
            if isinstance(data, list):
                for e in data:
                    if isinstance(e, dict) and str(e.get("id")) == mem_id:
                        raw = e.get("snippet") or e.get("text") or ""
                        sn = (raw[:120] + "...") if raw and len(raw) > 120 else (raw or "")
                        return sn, found_path
        except Exception:
            return "", ""
        return "", found_path or ""
    # Assemble output with optional meta snippets
    updated_meta = False
    if args.json:
        out = []
        for mid, score in hits:
            snippet = ""
            if mgr.meta_map and mid in mgr.meta_map:
                snippet = mgr.meta_map[mid].get("snippet", "")
            else:
                if store is not None:
                    entry = store.system.memory_entries.get(mid)
                    snippet = (entry.encoded_experience.raw_text[:120] + "...") if entry else ""
                elif getattr(args, "data", None):
                    snippet, src = _dir_snippet(mid)
                    if args.persist_meta and snippet:
                        mgr.meta_map[mid] = {"source": src, "snippet": snippet}
                        updated_meta = True
            out.append({"id": mid, "score": round(score, 6), "snippet": snippet})
        print(json.dumps(out, indent=2))
    else:
        for mid, score in hits:
            if mgr.meta_map and mid in mgr.meta_map:
                snippet = mgr.meta_map[mid].get("snippet", "")
            else:
                if store is not None:
                    entry = store.system.memory_entries.get(mid)
                    snippet = (entry.encoded_experience.raw_text[:120] + "...") if entry else ""
                else:
                    snippet, src = _dir_snippet(mid)
                    if args.persist_meta and snippet:
                        mgr.meta_map[mid] = {"source": src, "snippet": snippet}
                        updated_meta = True
            print(f"- id={mid} score={score:.3f} text={snippet}")

    # Persist meta map if requested
    if args.persist_meta:
        meta_path = args.index + ".meta.json"
        payload = {"dim": mgr.dim, "ids": getattr(mgr, "ids", []), "map": mgr.meta_map}
        try:
            # Merge with existing if present
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as mf:
                    old = json.load(mf)
                if isinstance(old, dict):
                    # prefer current dim/ids, but merge map entries
                    old_map = old.get("map") if isinstance(old.get("map"), dict) else {}
                    old_map.update(payload["map"])  # type: ignore
                    payload["map"] = old_map  # type: ignore
            with open(meta_path, "w", encoding="utf-8") as mf:
                json.dump(payload, mf, ensure_ascii=False, indent=2)
            print(f"Persisted meta to {meta_path}")
        except Exception as e:
            print(f"Warning: failed to persist meta: {e}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Episodic Memory CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Validate and summarize the JSON file")
    v.add_argument("path", help="Path to EpisodicMemorySystem.json")
    v.add_argument("--schema", nargs="?", const="auto", default=None, help="Validate against JSON Schema (provide path or use 'auto')")
    v.set_defaults(func=cmd_validate)

    s = sub.add_parser("search", help="Search memories by query text")
    s.add_argument("path", help="Path to EpisodicMemorySystem.json")
    s.add_argument("query", help="Query text")
    s.add_argument("--top-k", type=int, default=5)
    s.add_argument("--threshold", type=float, default=None, help="Override similarity threshold for this search")
    s.add_argument("--embedder", choices=["hash", "openai", "local"], default=None, help="Embedding backend for the query")
    s.add_argument("--openai-model", default=None, help="OpenAI embedding model (if using openai)")
    s.set_defaults(func=cmd_search)

    a = sub.add_parser("add", help="Add a new memory entry")
    a.add_argument("path", help="Path to EpisodicMemorySystem.json")
    a.add_argument("text", help="Raw text to store")
    a.add_argument("--tags", nargs="*", default=[], help="Context tags")
    a.add_argument("--importance", type=float, default=0.5)
    a.add_argument("--reward", type=float, default=0.0)
    a.add_argument("--tone", default="neutral")
    a.add_argument("--location", default="")
    a.add_argument("--user-id", default="")
    a.add_argument("--embedder", choices=["hash", "openai", "local"], default=None, help="Embedding backend for this add")
    a.add_argument("--openai-model", default=None, help="OpenAI embedding model (if using openai)")
    a.add_argument("--embed-dim", type=int, default=None, help="Embedding dimension override")
    a.set_defaults(func=cmd_add)

    sv = sub.add_parser("schema-validate", help="Validate file strictly against JSON Schema")
    sv.add_argument("path", help="Path to EpisodicMemorySystem.json")
    sv.add_argument("--schema", nargs="?", const="auto", default="auto", help="Schema path or 'auto'")
    sv.set_defaults(func=cmd_schema_validate)

    fx = sub.add_parser("fix", help="Fix and normalize file, optionally re-embed and rebuild indexes")
    fx.add_argument("path", help="Path to EpisodicMemorySystem.json")
    fx.add_argument("--in-place", action="store_true", help="Write changes back to the same file")
    fx.add_argument("--output", default=None, help="Optional output path")
    fx.add_argument("--schema", nargs="?", const="auto", default=None, help="Schema validation after fix")
    fx.add_argument("--embedder", choices=["hash", "openai", "local"], default=None, help="Embedding backend for re-embedding")
    fx.add_argument("--openai-model", default=None, help="OpenAI embedding model (if using openai)")
    fx.add_argument("--embed-dim", type=int, default=None, help="Target embedding dimension for fix")
    fx.add_argument("--reembed", action="store_true", help="Force re-embedding all entries")
    fx.set_defaults(func=cmd_fix)

    ib = sub.add_parser("index-build", help="Build a FAISS index for fast search")
    ib.add_argument("path", nargs="?", help="Path to a single EpisodicMemorySystem.json (positional)")
    ib.add_argument("index", nargs="?", help="Path to write FAISS index (positional, e.g., index.faiss)")
    ib.add_argument("--data", help="File or directory of JSON files to index")
    ib.add_argument("--output", help="Output FAISS index path (e.g., indexes/faiss.index)")
    ib.add_argument("--batch-size", type=int, default=1024)
    ib.add_argument("--sleep-ms", type=int, default=0, help="Sleep between batches to reduce CPU spikes")
    ib.set_defaults(func=cmd_index_build)

    isr = sub.add_parser("index-search", help="Search using a pre-built FAISS index")
    isr.add_argument("index", help="Path to FAISS index (.faiss)")
    isr.add_argument("query", help="Query text")
    isr.add_argument("--path", dest="path", default=None, help="Path to EpisodicMemorySystem.json for fallback snippets")
    isr.add_argument("--data", dest="data", default=None, help="Optional meta JSON file or directory root")
    isr.add_argument("--top-k", type=int, default=5)
    isr.add_argument("--min-score", type=float, default=None, help="Minimum score threshold for results (IP metric)")
    isr.add_argument("--max-distance", type=float, default=None, help="Maximum distance for L2 metric indexes")
    isr.add_argument("--embedder", choices=["hash", "openai", "local"], default=None)
    isr.add_argument("--openai-model", default=None)
    isr.add_argument("--json", action="store_true", help="Output JSON with snippets if available")
    isr.add_argument("--persist-meta", action="store_true", help="Write/normalize <index>.meta.json after search")
    isr.add_argument("--max-scan", type=int, default=2000, help="When using --data dir and no meta, limit file scans")
    isr.set_defaults(func=cmd_index_search)

    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
