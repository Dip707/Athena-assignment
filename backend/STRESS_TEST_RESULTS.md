# Backend stress-test results

Run on 2026-09-01 at 18:14 UTC from the repository root. The tree was at
`5d77da5` (`Allow local frontend origins`) before this stress-test commit.
Local ignored files were not touched.

## Commands and outcomes

```text
cd backend
./venv/bin/pytest -q tests/test_stress_backend.py
13 passed, 1 warning in 10.12s

./venv/bin/pytest -q
55 passed, 1 warning in 9.66s
```

The existing warning is Starlette's `httpx` TestClient deprecation warning.

## Scenarios covered

- Empty catalog readiness and zero-result search.
- Invalid `/index` payload rejected with `422` without replacing the catalog.
- Valid wholesale replacement reflected by `/catalog/status` and `/search`.
- Missing `GEMINI_API_KEY` leaves deterministic results untagged.
- Simulated Gemini client failure preserves the exact deterministic result list.
- Price/category extraction, soft-filter response shape, and no-match queries.
- Pagination/query validation (`422` for invalid bounds or missing query).
- Five repeated searches and twelve concurrent read-only searches with stable ordering.
- Prompt-injection-like product text preserved as data, with bounded result schema.
- Hybrid rank fields and BM25/semantic contribution explanations.

Dense retrieval and Gemini were intentionally isolated: semantic results were
mocked and no paid provider call or secret value was used. The bundled query
report remains explicitly marked `BM25 FALLBACK`; it must not be presented as
runtime-validated hybrid evidence until Qdrant and the local BGE model are
available.

## Edge observation

The current `rank_bm25` configuration returns zero-scored/no-match results for
very small catalogs where every query term occurs in the whole corpus (for
example, a one- or two-product replacement catalog). The intended three-plus
product replacement path is covered and passes. If single-item catalogs are a
product requirement, the ranker needs a fallback policy such as lexical
containment or a minimum-corpus guard.

No secrets, catalog files, or running server state were modified by this run.
