# AI Product Search — backend

FastAPI service for hybrid product search. Run commands in this document from
`backend/`.

## Setup and run

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # optionally set GEMINI_API_KEY locally
docker compose up -d        # Qdrant, needed for semantic retrieval
uvicorn app.main:app --reload
```

The service listens on `http://localhost:8000`. It loads
`../data/products.json` (the bundled catalog currently has 225 records) when
the file is present. If it is absent, the service starts with an empty
catalog; load a valid array through `/index` before searching. `GET
/catalog/status` reports whether a non-empty catalog is loaded and whether an
AI key is configured, without exposing the key.

## Retrieval pipeline

`app/data_loader.product_text()` supplies the same complete text to both
retrievers: `title + description + category`.

- BM25 is an in-process lexical index (`app/search/bm25.py`).
- Semantic retrieval uses local `BAAI/bge-small-en-v1.5` embeddings in the
  Qdrant `products` collection with cosine distance. Query text is prefixed
  exactly with `Represent this sentence for searching relevant passages: `.
- The API takes up to 50 candidates from each retriever and combines ranks via
  weighted RRF (`alpha=1.0`, `beta=1.0`, `k=60`). Missing-list contributions
  are zero. Responses expose ranks, raw scores, fused score, and contribution
  explanations.
- Price ceilings and catalog-derived category hints are symmetric soft
  penalties: each mismatch multiplies `fused_score` by `0.15`, penalties stack,
  and no product is removed.

If Qdrant or the embedding model is unavailable at startup or query time, the
semantic leg is disabled and search continues BM25-only. This is a runtime
degradation mode, not semantic readiness without the required infrastructure.

## HTTP contract

- `GET /health` returns `{"status":"ok"}`.
- `GET /catalog/status` returns `loaded`, `product_count`, and boolean
  `ai_enabled`.
- `GET /search?q=...&page=1&page_size=10&curate=true` returns a
  `SearchResponse`. `curate` defaults to `true`; callers may use
  `curate=false` for deterministic-only output. Pagination follows fusion,
  penalties, and optional curation. `total_results` is capped by the 50-item
  candidate retrieval, so it is not a full-catalog match count.
- `POST /index` accepts a raw JSON array of records shaped as
  `{id, title, description, category, price}`. It synchronously and wholesale
  replaces the active catalog and rebuilds BM25 and Qdrant. The endpoint is
  unauthenticated for this assignment/demo. If embedding rebuild fails, BM25
  remains available and the response still reports `{"indexed": n}`.

The frontend dataset loader accepts a JSON file or pasted JSON and sends the
same array to `/index`.

## Optional curation and configuration

When `GEMINI_API_KEY` is present (loaded from gitignored `backend/.env`), the
service makes at most one `select_curated_results` function-calling request to
`gemma-4-26b-a4b-it` using a 10-second provider timeout. It receives the query,
detected filters, and candidate title/category/price. Every pick is validated
against candidate IDs and actual fields. Missing key, timeout, provider/API
error, malformed output, or failed validation rejects the whole curation
response and returns the complete deterministic ranking unchanged.

`QDRANT_HOST` and `QDRANT_PORT` default to `localhost` and `6333`. No API key
is needed for BM25; the local model may need a first-time network download.

## Tests and report

```bash
./venv/bin/pytest -q
./venv/bin/python scripts/run_test_queries.py
```

The suite currently contains 38 tests across 10 modules (including
`tests/__init__.py`) and may show a Starlette/httpx deprecation warning. The
checked-in `TEST_RESULTS.md` is a 10-query capture; read its provenance block
before interpreting it. Null semantic ranks indicate BM25 fallback, not
validated hybrid retrieval, and the report must not imply live Gemini success
without evidence. Regenerated reports should add command, timestamp,
commit/tree state, model/Qdrant status, curation mode, and key-presence-only
metadata.
