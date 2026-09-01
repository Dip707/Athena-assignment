# Architecture

## Request flow

```text
Natural-language query
        |
        +--> BM25 lexical retrieval --------+
        |                                    |
        +--> BGE embeddings + Qdrant --------+--> Reciprocal Rank Fusion
                                                     |
                                              soft constraint penalties
                                                     |
                                            optional Gemma curation
                                                     |
                                               SearchResponse
```

The API indexes the same `title + description + category` text for both
retrievers. BM25 rewards exact term overlap. The local
`BAAI/bge-small-en-v1.5` model embeds products and queries so conceptually
related products can match even when wording differs. Query embeddings use
the model's retrieval instruction:

```text
Represent this sentence for searching relevant passages: <query>
```

Vectors are searched in a local Qdrant collection with cosine similarity.
If the model or Qdrant is unavailable, the service remains usable through the
BM25 leg and exposes null semantic ranks rather than pretending hybrid search
ran successfully.

## Ranking

Each retriever contributes up to 50 candidates. Their rank positions are
combined with Reciprocal Rank Fusion:

```text
score = 1 / (60 + bm25_rank) + 1 / (60 + semantic_rank)
```

A missing rank contributes zero. Rank-based fusion avoids normalizing BM25
and cosine scores, which live on different numeric scales. See
[`RANKING_EXPLANATION.md`](../RANKING_EXPLANATION.md) for the full formula,
soft-penalty behavior, response fields, and a worked example.

Queries can express a maximum price and a category hint. These are applied as
soft constraints after fusion: each mismatch multiplies the score by `0.15`,
and two mismatches stack. Results are never silently discarded, so the API can
still expose near alternatives while strongly preferring in-constraint items.

## Optional AI curation

Gemma is a presentation layer, not a retriever. The backend sends the query,
detected constraints, and top deterministic candidates in a single structured
function-calling request. It can label and reorder eligible candidates but
cannot invent products or alter their ranking evidence.

Every returned product ID and category/price claim is validated against the
catalog. A missing API key, timeout, malformed response, invalid selection, or
provider error returns the deterministic list unchanged. The frontend first
requests `curate=false` and renders immediately, then requests the optional
curated view only when the backend reports AI is enabled.

## Catalog lifecycle

At startup, the backend loads `data/products.json`. `POST /index` accepts a raw
JSON array containing `id`, `title`, `description`, `category`, and `price`,
then atomically replaces the in-memory catalog and rebuilds retrieval indexes.
The frontend exposes the same flow through paste and file-upload controls.

Semantic-index rebuild failure does not discard the valid catalog or BM25
index. The status endpoint reports whether a catalog is loaded, its product
count, and whether optional AI curation is configured without exposing the
credential.

## Component boundaries

```text
backend/app/
  main.py                 HTTP routes and request orchestration
  catalog_store.py        active catalog and retriever lifecycle
  data_loader.py          JSON validation and shared product text
  models.py               request and response schemas
  search/
    bm25.py               lexical retrieval
    embeddings.py         BGE encoding and Qdrant retrieval
    fusion.py             reciprocal-rank fusion
    filters.py            query constraints and soft penalties
    curator.py            optional structured Gemma curation

frontend/src/
  App.jsx                 catalog readiness and progressive search flow
  api.js                  backend client
  components/             dataset loader, search controls, and results
```

## Deliberate trade-offs

- The catalog and BM25 index are in process, which keeps the assignment simple
  but is not shared across multiple API workers.
- Category detection uses deterministic token overlap against the current
  catalog. It is explainable and dataset-aware, but weaker than a trained
  intent classifier for brand-to-category relationships.
- Fusion constants and penalties are documented defaults rather than values
  tuned on relevance labels; no labeled evaluation set was supplied.
- `POST /index` is intentionally unauthenticated for the local demo. A
  production service would add authorization, durable storage, background
  indexing, and versioned catalog swaps.
