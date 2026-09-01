# Ranking explanation

This document explains how `GET /search` turns a natural-language product
query into an ordered response. The ranking shown by the API is a deterministic
retrieval ranking; the optional AI step is a presentation refinement layered on
top of it.

## 1. Product representation

The catalog is loaded from `data/products.json` at startup. `POST /index` can
replace it with a JSON array containing `id`, `title`, `description`,
`category`, and `price` fields. For every product, both retrieval paths use the
same text:

```text
title + " " + description + " " + category
```

Including the category in this shared text lets both exact lexical matches and
semantic matches use category information. The catalog is held in memory after
loading; `/index` rebuilds the indices synchronously.

## 2. Candidate retrieval

Each search request independently asks both retrievers for at most 50
candidates (`CANDIDATE_TOP_K = 50`). A retriever returns a one-indexed rank and
its native score for each product.

### BM25 lexical retrieval

BM25 uses `rank_bm25.BM25Okapi` in the backend process. Product text and the
query are lowercased and tokenized into alphanumeric tokens. Products whose
BM25 score is zero are omitted, because they share no token with the query.
The raw BM25 score is retained for explanation, but it is not added directly to
the semantic score.

### Dense semantic retrieval

The semantic path uses the local
`BAAI/bge-small-en-v1.5` sentence-transformers model. Product text is encoded
as-is when the Qdrant index is built. Query text is encoded with this exact BGE
instruction prefix:

The exact prefix is `Represent this sentence for searching relevant passages: `
(the space before the closing backtick is part of the string).

The vectors are stored in the local Qdrant collection `products`, configured
with cosine distance. Qdrant returns cosine similarity (higher is closer), and
that native value is retained as `semantic_score`. The raw cosine and BM25
values have different numeric scales, so neither is combined with the other
directly.

If Qdrant or the local model is unavailable, the service continues with the
BM25 list. In that case `semantic_rank` and `semantic_score` are `null`, and
the semantic contribution is zero; such a response is BM25-only evidence.

## 3. Deterministic weighted RRF

The union of product IDs returned by either retriever is fused. The production
defaults are `alpha = 1.0`, `beta = 1.0`, and `k = 60`. For product `p`:

```text
bm25_contribution(p)     = alpha / (k + bm25_rank(p))
semantic_contribution(p) = beta  / (k + semantic_rank(p))
fused_score(p)           = bm25_contribution(p) + semantic_contribution(p)
```

If a product is absent from one list, that list contributes exactly `0`; no
synthetic rank is assigned. This rank-based formula avoids normalizing
unbounded BM25 scores against cosine similarities. Products not present in the
currently loaded catalog are discarded. The fused list is ordered by
descending `fused_score`, with product ID as the deterministic tie-breaker at
this stage.

## 4. Natural-language constraints as soft penalties

The query parser extracts two optional constraints before penalties are
applied:

- A price ceiling from phrases such as `under ₹5000`, `below 5000`, or
  `less than Rs. 5,000`.
- A category hint by token overlap with categories in the currently loaded
  catalog. Matching ignores the stopword `gaming` and folds a trailing `s`
  for simple singular/plural matching. A tie is resolved alphabetically.

These are ranking signals, not hard filters. After RRF:

- If `product.price > price_max`, multiply `fused_score` by `0.15`.
- If `product.category != category_hint`, multiply `fused_score` by `0.15`.
- If both conditions are true, apply both multipliers:
  `fused_score × 0.15 × 0.15`.

No product is removed for violating a constraint. The result list is sorted
again by the resulting score. Pagination then slices that ordered list using
zero-based offset `(page - 1) * page_size`; the default is page 1 with 10
results. `total_results` is the size of the fused candidate union after
penalties, not a full-catalog count. Since each retriever is capped at 50, the
union can contain at most 100 candidates before pagination.

## 5. Worked example

Consider the query `mechanical keyboard under ₹5000`, with the currently loaded
catalog producing the category hint `Gaming Keyboards`. Suppose the two
retrievers return these ranks (native scores are shown only for transparency):

| Product | Price/category | BM25 rank, score | Semantic rank, cosine | RRF before penalties | Penalties | Final score |
|---|---|---:|---:|---:|---|---:|
| A — Mechanical Keyboard | ₹3,999 / Gaming Keyboards | 1, 5.0 | 1, 0.90 | `1/61 + 1/61 = 0.032786885` | none | `0.032786885` |
| B — Premium Mechanical Keyboard | ₹8,999 / Gaming Keyboards | 2, 3.0 | 3, 0.50 | `1/62 + 1/63 = 0.032002048` | price × 0.15 | `0.004800307` |
| C — PlayStation Gift Card | ₹9,000 / Gift Cards | 3, 1.0 | 2, 0.70 | `1/63 + 1/62 = 0.032002048` | price × 0.15, category × 0.15 | `0.000720046` |

Thus the deterministic order is A, B, C. B initially has a strong retrieval
score but falls below A because it exceeds the price ceiling. C violates both
constraints, so its score is multiplied by `0.0225` in total. The BM25 and
cosine scores themselves do not determine the fusion arithmetic; only their
retriever ranks do.

The corresponding explanation fields are designed to make this calculation
inspectable. Values below are illustrative JSON for product B:

```json
{
  "product": {
    "id": 2,
    "title": "Premium Mechanical Keyboard",
    "description": "Hot-swappable mechanical keyboard",
    "category": "Gaming Keyboards",
    "price": 8999
  },
  "bm25_rank": 2,
  "semantic_rank": 3,
  "bm25_score": 3.0,
  "semantic_score": 0.5,
  "fused_score": 0.004800307,
  "tag": null,
  "explanation": {
    "bm25_contribution": 0.016129,
    "semantic_contribution": 0.015873,
    "price_penalty_applied": true
  }
}
```

`bm25_rank` and `semantic_rank` are one-indexed and can be `null` when a
product was absent from that retriever. `bm25_score` and `semantic_score` are
the retrievers' native values. `fused_score` is the post-penalty score used for
deterministic ordering. The contribution values are rounded to six decimal
places in the API explanation. Penalty flags appear only when that penalty was
applied; a product violating both constraints has both flags.

## 6. Optional AI curation is not ranking

When `curate=true` (the API default), the already ranked and penalized top 10
candidates are sent to one optional Gemini API call using Gemma
`gemma-4-26b-a4b-it`. The versioned system prompt asks for exactly one
`select_curated_results` function call. The model may select up to four
presentation slots:

- `best_match`
- `best_outside_category`
- `best_near_price` (strictly above the ceiling and within 10%)
- `best_outside_both`

The server validates the response before using it: every ID must be in the
top-10 candidate pool, slots and IDs must be unique, `best_match` is required,
and each category/price claim is checked against the actual product fields.
Valid picks receive a display `tag` and move to the front; the remaining
products retain their deterministic order. Curation does not recalculate or
modify `bm25_score`, `semantic_score`, `fused_score`, or the explanation
fields. It changes presentation order and labels only.

The curation request has a 10-second provider timeout and reads
`GEMINI_API_KEY` from the local environment (`backend/.env` is gitignored).
The key is never part of this repository, prompts, reports, or responses. If
the key is missing, the provider errors or times out, the response is malformed,
or validation fails, the complete deterministic ranking is returned unchanged.
Consequently, `curate=false` is the clearest way to inspect the pure ranking,
while `curate=true` is an optional presentation layer over that same ranking.

The frontend intentionally requests `curate=false` first so deterministic
results appear immediately, then makes the best-effort `curate=true` request
when AI is available. A failed refinement leaves the first result set intact.

## Source files

- Retrieval and route orchestration: `backend/app/main.py`
- Product text and loading: `backend/app/data_loader.py`
- BM25: `backend/app/search/bm25.py`
- BGE/Qdrant semantic search: `backend/app/search/embeddings.py`
- RRF: `backend/app/search/fusion.py`
- Filter extraction and penalties: `backend/app/search/filters.py`
- Optional curation and validation: `backend/app/search/curator.py`
- API schemas: `backend/app/models.py`
- Static curation prompt: `backend/app/prompts/curation_system_prompt.txt`
