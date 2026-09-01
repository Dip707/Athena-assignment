# AI Product Search Engine

An assignment-ready hybrid product search application. A FastAPI backend
combines lexical BM25 retrieval with local BGE embeddings in Qdrant, applies
catalog-derived soft filter penalties, and can optionally add one best-effort
Gemma curation pass. A React/Vite frontend loads catalogs and displays the
ranked results with ranking explanations.

## Quick start

1. Start Qdrant:

   ```bash
   cd backend
   docker compose up -d
   ```

2. Install and run the backend:

   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env       # optionally add GEMINI_API_KEY locally
   uvicorn app.main:app --reload
   ```

   The API listens on `http://localhost:8000`. The bundled
   `data/products.json` catalog (225 products) is loaded at startup when it is
   present. If the file is unavailable, the service starts with an empty
   catalog; use the UI loader or `POST /index`, then confirm readiness with
   `GET /catalog/status`.

3. Install and run the frontend in another terminal:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   Open `http://localhost:5173`. The frontend API base is currently the
   literal `http://localhost:8000` in `frontend/src/api.js`.

## Search behavior

Both retrievers index the shared `title + description + category` text. The
semantic leg uses the local `BAAI/bge-small-en-v1.5` sentence-transformers
model; queries are encoded with the BGE instruction
`Represent this sentence for searching relevant passages: `. BM25 and
semantic results are combined by weighted Reciprocal Rank Fusion with
`alpha=1.0`, `beta=1.0`, and `k=60`. A product missing from one list gets no
contribution from that retriever, rather than being removed.

Price ceilings and catalog-derived category hints are applied as symmetric
soft penalties. Each mismatch multiplies `fused_score` by `0.15`; both
mismatches stack, and no result is hard-excluded. Responses include retriever
ranks, scores, contribution explanations, and penalty flags.

The API defaults to `curate=true`. Curation makes at most one
function-calling request to `gemma-4-26b-a4b-it` through the Gemini API, with a
10-second provider timeout. It only tags/reorders eligible candidates; a
missing key, timeout, API error, malformed response, or failed validation
silently returns the deterministic ranking unchanged. Direct callers can set
`curate=false` for deterministic-only output.

The UI makes two requests for each search action: first `curate=false` so
deterministic results appear quickly, then `curate=true` for best-effort AI
refinement when the backend has `ai_enabled=true`. With no key, the second
request is a safe no-op. If refinement fails, the first result set is
retained. A generation guard prevents an older search response from
overwriting a newer one, so this progressive flow is an intentional invariant
rather than an extra ranking mode.

## API

- `GET /health` returns `{"status":"ok"}`.
- `GET /catalog/status` reports `loaded`, `product_count`, and boolean
  `ai_enabled` without exposing the Gemini key.
- `GET /search?q=...&page=1&page_size=10&curate=true` returns a
  `SearchResponse`. Each request retrieves at most 50 candidates from each
  retriever before fusion; therefore `total_results` is the number of fused
  candidates returned by this capped pipeline, not a full-catalog match
  count.
- `POST /index` accepts a raw JSON array of
  `{id, title, description, category, price}` records and synchronously
  replaces the active in-memory catalog while rebuilding BM25 and Qdrant.
  It is unauthenticated and intended for the assignment/demo; an embedding
  rebuild failure still leaves BM25 available and returns `{"indexed": n}`.

If Qdrant or the local model is unavailable during startup or a query, the
semantic leg is disabled and search proceeds BM25-only. The backend still
starts in that degraded state. The bundled catalog can be replaced in the UI
with the dataset loader or by calling `/index` directly.

## Tests and deliverables

Run the backend suite from `backend/`:

```bash
./venv/bin/pytest -q
```

Run the 10-query report (with Qdrant/model available when semantic evidence is
required):

```bash
./venv/bin/python scripts/run_test_queries.py
```

The assignment artifacts are easy to find:

- [Test input/output](backend/TEST_RESULTS.md) — generated query report;
  inspect its provenance block before interpreting semantic or AI claims.
- [Ranking explanation](RANKING_EXPLANATION.md) — deterministic BM25 + BGE
  retrieval, weighted RRF, soft penalties, API explanation fields, and the
  optional curation boundary.
- [Assumptions](ASSUMPTIONS.md) — design intent, safety boundaries, and
  environment-limited evidence.
- [AI prompt log](AI_PROMPTS.md) — prompt text, model configuration, and
  development-use provenance.
- [Backend guide](backend/README.md) and [frontend guide](frontend/README.md).
- [Architecture](docs/ARCHITECTURE.md) — request flow, component boundaries,
  failure behavior, and trade-offs.

The generated report's provenance should identify its command and timestamp,
git/tree state, embedding model and semantic/Qdrant status, curation mode,
and the fact that key presence—not the key value—was recorded. The checked-in
10-query capture explicitly records BM25 fallback and key-presence-only AI
mode; a report with `semantic_rank: null` is BM25-only evidence and must not
be described as a validated hybrid run.

## Configuration and safety

`GEMINI_API_KEY` is optional and loaded from the gitignored
`backend/.env`. Qdrant uses `QDRANT_HOST=localhost` and
`QDRANT_PORT=6333` by default. Never commit a real key or place one in
documentation, prompts, source, or test output. Catalog descriptions are
untrusted input to curation; the static system prompt labels them as data, and
server-side validation checks every model pick against the candidate IDs and
actual product fields.
