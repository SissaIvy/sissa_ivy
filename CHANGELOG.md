# Changelog

All notable changes to this project will be documented in this file.

## v0.2.0 (2025-09-09)

Stabilization and UX improvements following rc1.

Added
- CLI: `search --embedder {hash,openai,local}` and `--openai-model`; threaded embedder to `MemoryStore.search` for correct query embedding.
- Tests: CLI search flag coverage (`tests/test_cli_search_embedder_flag.py`).
- CI: lightweight CLI smoke job validating search with `--embedder hash`.

Changed
- Packaging: constrain package discovery to `episodic_memory` for reliable editable installs.
- FAISS index build: ensure output directory exists before saving index.
- `index-search`: prints a warning when `--max-distance` is used with IP/cosine indexes.
- Service version bumped to 0.2.0.

## v0.2.0rc1 (2025-09-08)

Highlights
- Governance integrated end-to-end: schema, models, persistence, and fixer merge from preamble.
- Pluggable embeddings with caching: built-in hash (deterministic), OpenAI (optional), and local Sentence-Transformers.
- ANN search ready: FAISS index build/search with batching and sleep to smooth CPU usage.
- API Server: FastAPI endpoints for validate, search, and add.
- Robust validation: JSON Schema packaged with `FormatChecker`; fixer is idempotent.

Added
- `governance` to root model and JSON Schema with provenance, retention policy, and access control.
- `episodic_memory/embeddings.py`: Hash, OpenAI, and Sentence-Transformers embedders; `CachedEmbedder` with SQLite cache.
- `episodic_memory/cache.py`: SQLite cache (WAL, busy timeout) for CPU/network smoothing.
- `episodic_memory/faiss_index.py`: FAISS manager (build/search, batch controls).
- `server.py`: FastAPI app with `/health`, `/validate`, `/search`, `/add`.
- CLI commands: `schema-validate`, `fix`, `index-build`, `index-search`.
- GitHub Actions CI: lint (ruff) and tests across 3.9–3.11.

Changed
- Deterministic `_hash_embed` (sha256 n‑grams) replaces salt-random `hash()` usage.
- Schema validation now enforces formats via `Draft202012Validator` + `FormatChecker`.
- `index-search` uses FAISS index dimension for query embedding to avoid mismatches.
- Schema loading via `importlib.resources` for packaging safety.

Fixed
- Fixer idempotency validated by unit test.
- Temporal/index rebuild consistency improvements.

Performance
- Embedding cache with WAL + busy timeout to reduce contention and spikes.
- FAISS index builder supports batching and `--sleep-ms` to smooth CPU load.
- API uses a semaphore to cap concurrent embeddings.

Security
- Optional OpenAI usage; no keys logged. Recommend setting `OPENAI_API_KEY` in environment.

Migration Notes
- Run `episodic-memory fix <file> --in-place` once to rebuild indexes and align embedding dimensions.
- If using FAISS, rebuild indexes after re-embedding.

---

## v0.1.0 (Initial)
- Initial minimal store, loader, retrieval, CLI, and tests.
