# Assumptions and boundaries

This file separates intended design behavior from what can be proven in a
particular local environment.

## Design assumptions

- Retrieval is local and deterministic: BM25 and
  `BAAI/bge-small-en-v1.5` embeddings index `title + description + category`.
  The BGE query is prefixed with
  `Represent this sentence for searching relevant passages: `. No query-time
  embedding API key is required, although first-time model setup may need a
  network download.
- Qdrant is the local vector store. `QDRANT_HOST` defaults to `localhost`
  and `QDRANT_PORT` to `6333`. If Qdrant or the model is unavailable, the
  semantic leg degrades to BM25-only; this does not make semantic search
  available without its infrastructure.
- Weighted RRF uses fixed `alpha=1.0`, `beta=1.0`, `k=60`. Missing-
  retriever contributions are zero. The two retrievers each provide at most
  50 candidates to the route before fusion.
- A detected price ceiling or category hint is a soft constraint. A mismatch
  multiplies `fused_score` by `0.15`; mismatches stack multiplicatively and
  no product is removed. Category hints come from token overlap against the
  currently loaded catalog, with naive singular/plural folding and `gaming`
  ignored as a stopword.
- `POST /index` synchronously and wholesale replaces the active catalog and
  rebuilds BM25 and the embedding collection. It is unauthenticated and is
  suitable for this assignment/demo, not a production deployment. If the
  embedding rebuild fails, the catalog remains searchable through BM25.
- Curation is one optional function-calling request to Gemma
  `gemma-4-26b-a4b-it` via `google-genai`, with a provider timeout of 10
  seconds. It is presentation-layer tagging/reordering, not a replacement
  for deterministic ranking. Missing key, provider failure, timeout,
  malformed output, or validation failure returns the complete deterministic
  candidate list unchanged.
- The curation input contains the query, detected filters, and candidate
  `title`, `category`, and `price`. Uploaded descriptions remain untrusted
  retrieval/catalog data but are deliberately omitted from
  `_build_user_content()`.
- Every model pick is validated against the fixed candidate IDs and actual
  category/price fields. A failed claim rejects the entire curation response;
  it does not partially drop one pick or alter the deterministic list.
- The frontend intentionally performs `curate=false` followed by
  `curate=true` for one user search. Deterministic results are shown first
  and retained if refinement fails; generation guards prevent stale requests
  from winning.
- The bundled catalog is synthetic and currently contains 225 products. A
  runtime upload can replace it with any valid JSON array of product records.

## Environment-limited evidence

- A local test run on 2026-09-01 produced 38 passing backend tests and one
  Starlette/httpx deprecation warning. That verifies unit/integration behavior
  in the checked-out environment, not availability of an external Gemini key,
  Qdrant service, or a fresh model download.
- `backend/TEST_RESULTS.md` is a generated artifact. Its provenance block is
  authoritative for the environment that produced that specific file. Null
  semantic ranks mean the displayed report is BM25-only; they are not proof
  that the hybrid path was exercised. Likewise, absent AI tags mean the
  report did not demonstrate successful curation.
- No claim in this repository should imply a live Gemini success, semantic
  readiness, or production security unless the corresponding provenance and
  runtime evidence are present.
