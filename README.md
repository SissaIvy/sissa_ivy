Episodic Memory System (Python)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Overview
- Robust loader that extracts the last valid JSON object from files that may contain extra fragments.
- Typed, dependency-free models and a `MemoryStore` API to add, save, and search memories.
- Simple hash-based embeddings to enable demo retrieval without external services.
- CLI for validation, search, and adding memories.
 - JSON Schema for validation and a `fix` command to normalize files.
 - Pluggable embeddings: built-in hash (default) and OpenAI backend (optional).

Quick Start
- Validate the sample file:
  - `python memory_cli.py validate EpisodicMemorySystem.json`
  - With schema: `python memory_cli.py validate EpisodicMemorySystem.json --schema`
- Search (override threshold for the demo):
  - `python memory_cli.py search EpisodicMemorySystem.json "episodic" --threshold 0.1`
  - Choose query embedder when needed (use the same backend used to build vectors):
    - Hash: `python memory_cli.py search EpisodicMemorySystem.json "episodic" --embedder hash`
    - OpenAI: `python memory_cli.py search EpisodicMemorySystem.json "episodic" --embedder openai --openai-model text-embedding-3-small`
    - Local ST: `python memory_cli.py search EpisodicMemorySystem.json "episodic" --embedder local`
- Add a memory and persist:
  - `python memory_cli.py add EpisodicMemorySystem.json "My new memory" --tags test foo --importance 0.6`
  - With OpenAI embeddings: `python memory_cli.py add EpisodicMemorySystem.json "My new memory" --embedder openai --openai-model text-embedding-3-small`
    - Requires `OPENAI_API_KEY` in env and installing optional dep: `pip install -e .[openai]`

Fix and Normalize
- Fix inconsistencies (counts, indexes), optionally re-embed and write back:
  - Dry run to new file: `python memory_cli.py fix EpisodicMemorySystem.json --output fixed.json --schema`
  - In-place: `python memory_cli.py fix EpisodicMemorySystem.json --in-place --schema`
  - Force re-embed with OpenAI at 512 dims: `python memory_cli.py fix EpisodicMemorySystem.json --in-place --reembed --embedder openai --openai-model text-embedding-3-small --embed-dim 512`

Schema-Only Validation
- `python memory_cli.py schema-validate EpisodicMemorySystem.json` (auto-loads bundled schema)

Tests
- Run tests:
  - `python -m unittest discover -s tests -p "test_*.py" -v`

Packaging
- Build/install locally:
  - `pip install -e .`
  - CLI entrypoint: `episodic-memory` (mirrors `python memory_cli.py`)

API Server
- Install API extras: `pip install -e .[api]`
- Run: `uvicorn server:app --host 0.0.0.0 --port 8000`
- Endpoints:
  - `GET /health`
  - `POST /validate` { path or data, schema: true }
  - `POST /search` { path, query, top_k, threshold? }
  - `POST /add` { path, text, tags[], importance, reward, tone, embedder?, openai_model?, embed_dim? }

Programmatic Version
- In Python: `import episodic_memory as em; print(em.__version__)` (e.g., `0.2.0`)

ANN Index (FAISS)
- Build from a single file:
  - `episodic-memory index-build EpisodicMemorySystem.json index.faiss --sleep-ms 5`
- Build from a directory of JSON files:
  - `episodic-memory index-build --data path/to/data/ --output indexes/faiss.index --batch-size 256 --sleep-ms 50`
- Search with a prebuilt index:
  - `episodic-memory index-search indexes/faiss.index "episodic" --top-k 3`
  - Note: when indexing a directory, result IDs are `file.json::memory_id`. Snippets may be empty unless you look up the source file. Use `--data` to supply a meta file or directory for snippets.

Index Search Flags & Behavior
- `episodic-memory index-search <index> "<query>" [options]`

- `--data <path>`: accepts either
  - path to a `<index>.meta.json` file (fast); or
  - directory root (will look for `<index>.meta.json` adjacent to the index; otherwise performs a bounded scan).
- `--persist-meta`: when resolving snippets via a directory scan, write a normalized sidecar `<index>.meta.json` next to the index for fast future lookups.
- `--max-scan <N>` (default `2000`): upper bound on the number of files to scan when building ephemeral metadata; avoids accidental full-corpus scans.
- `--min-score <float>`: filter results by minimum inner-product score (useful for normalized IP indexes).
- `--max-distance <float>`: filter results by max L2 distance (for L2 indexes).
- `--top-k <N>`: number of nearest neighbors to retrieve.

Tip: When using IP/cosine indexes (e.g., IndexFlatIP), `--max-distance` is ignored and a warning is printed. Use an L2 index to apply a max-distance filter.

Example (persist meta after resolving snippets from a data directory):

```bash
episodic-memory index-search indexes/faiss.index "episodic" --top-k 5 --data path/to/data/ --persist-meta
```

Example (filter by minimum score with normalized IP index):

```bash
episodic-memory index-search indexes/faiss.index "episodic" --top-k 10 --min-score 0.2 --data path/to/data/
```

Embedding Backends
- Hash (default): No dependencies, deterministic, dimension configurable.
- OpenAI (optional): Set `OPENAI_API_KEY`, install `pip install -e .[openai]`, choose model via `--openai-model` or env `OPENAI_EMBEDDING_MODEL`.

Notes
- The included embedding is a placeholder. Swap `_hash_embed` in `episodic_memory/store.py` with a production embedding model or a vector DB integration for commercial deployments.
- The loader tolerates extra JSON fragments by extracting the final valid object; keep files clean in production.
 - The fixer rebuilds clusters and temporal index to align with embeddings and metadata.

Project Setup (GitHub Projects v2 Automation)
- This repo auto-adds Issues/PRs to a Projects v2 board and sets fields from labels/lifecycle.

1) Configure repository variables (Settings → Actions → Variables)
- `ORG_LOGIN`: org or user login (e.g., YourOrg or your-username)
- `PROJECT_NUMBER`: project number (e.g., 1)
- `PROJECT_OWNER_TYPE`: `org` (default) or `user`
- `SET_ITERATION`: `true`/`false` (default `false`)

2) Ensure Project fields exist (single-select, exact names)
- Status: Backlog, In Progress, Review, Done
- Type: Feature, Enabler, Spike, Bug

3) Label → field mapping
- `feature` → Type=Feature; `enabler` → Type=Enabler; `spike` → Type=Spike; `bug` → Type=Bug
- Status: default Backlog; `status:in-progress` → In Progress; `status:review` → Review; `status:done` or closed → Done

4) 60-second validation
- Manually dispatch workflow (Actions → Project Automation → Run)
- Open an Issue with label `feature` → appears with Type=Feature, Status=Backlog
- Add label `status:in-progress` → moves to In Progress
- Close the Issue → Status=Done

5) Iteration assignment (optional)
- If `SET_ITERATION=true` and the Project has an Iteration field, the workflow can assign the current iteration. Adjust `FIELD_ITERATION_NAME` env in the workflow if your field name differs.

## License
This project is licensed under the [Apache 2.0 License](LICENSE).

## Suntari Allegory (Closed‑Loop SOC)
- Guide: `docs/Suntari_Allegory_Closed_Loop_SOC.md`
- Cast & Roles appendix: `docs/Suntari_Cast_and_Roles.md`

### Cost & ROI knobs
Runs can report blended per‑event cost, token cost, and ROI/ROE in their JSON outputs. Set env vars locally (or inject into Azure ML jobs). See `README-aml.md` → “Cost & ROI knobs”.

Quick local example
```bash
export COST_APIM_MONTHLY=60 COST_EXPECTED_EVENTS_MONTH=100000
python closed_loop_security.py --profile strict --events events.json
```
Inspect `meta.costs` and `meta.roi` in the output for per‑run budgets and savings.
