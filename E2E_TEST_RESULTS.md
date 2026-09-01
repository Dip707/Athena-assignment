# End-to-end smoke results

This is a lightweight, repeatable HTTP smoke test for the locally running
backend and Vite frontend. It never calls Gemini, prints credentials, or
mutates the catalog with `POST /index`.

Run from the repository root:

```bash
./scripts/e2e_smoke.sh
```

Optional URLs:

```bash
./scripts/e2e_smoke.sh http://localhost:8000 http://localhost:5173
```

The checks cover health, catalog readiness, deterministic search with the
bundled catalog, pagination validation, no-match behavior, local CORS
preflight, and frontend reachability. AI curation is intentionally excluded;
the product is expected to work without a Gemini key.

## Latest local run

- Command: `./scripts/e2e_smoke.sh`
- Timestamp: 2026-09-01 (local Asia/Kolkata session; rerun after services restart)
- Result: pending live service restart; the previous run correctly failed at
  `/health` when `localhost:8000` was unavailable
- Backend: not yet re-run in this shell session
- Frontend: not yet re-run in this shell session
- Catalog: not asserted while backend is unavailable
- Embeddings/Qdrant: not asserted by this smoke test; inspect catalog/search
  diagnostics or `backend/TEST_RESULTS.md` for retrieval provenance
- Curation: not called; no Gemini credential required

To refresh this evidence, rerun the command and update the timestamp and
observations above.
