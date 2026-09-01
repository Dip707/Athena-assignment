# AI Product Search — frontend

React/Vite frontend for the product-search assignment. Run commands in this
document from `frontend/`.

## Setup and run

```bash
npm install
npm run dev
```

The dev server is normally at `http://localhost:5173`. The API client in
`src/api.js` currently uses the literal backend URL
`http://localhost:8000`; there is no frontend environment-variable override.
The backend must be running first.

```bash
npm run lint
npm run build
npm run preview
```

## User flows

`DatasetLoader` accepts either a JSON file or pasted JSON. The payload must be
a JSON array of records shaped like:

```json
[{"id": 1, "title": "...", "description": "...", "category": "...", "price": 1999.0}]
```

Loading calls unauthenticated `POST /index`, replaces the active backend
catalog for the current session, and synchronously rebuilds its indices. A
successful upload reports the indexed count; validation or network errors are
shown inline.

`SearchBar` submits a non-empty query. `App` makes two backend requests for a
single search: `GET /search?...&curate=false` first, so deterministic results
appear quickly, followed by `curate=true` for best-effort AI refinement when
the backend has AI enabled. With no key, the second request is a safe no-op. A
generation guard prevents stale responses from replacing a newer search, and
refinement failure silently retains the deterministic results. This means one
UI action can incur the extra latency and API call of refinement.

`ResultsList` renders idle, empty, and result states. `ProductCard` shows the
product and an expandable ranking explanation. BM25/semantic ranks and fused
score are populated when returned by the backend; a null semantic rank is
legitimate when semantic retrieval is unavailable or that product was absent
from the semantic candidate list. AI tags appear only when curation returns
validated picks.

## Backend response shape

`GET /search` returns `query`, `results`, `applied_filters`, `total_results`,
`page`, and `page_size`. Each result contains `product`, retriever ranks and
scores, `fused_score`, optional `tag`, and an `explanation` object containing
RRF contributions and any soft-penalty flags. The route retrieves at most 50
candidates from each retriever before fusion.

For direct deterministic requests, use `curate=false`; the backend default is
`curate=true`. The frontend's API base and `curate` query parameter behavior
are implemented in `src/api.js`.

## Project structure

```text
src/
  api.js
  App.jsx / App.css
  components/
    DatasetLoader.jsx / DatasetLoader.css
    SearchBar.jsx / SearchBar.css
    ResultsList.jsx / ResultsList.css
    ProductCard.jsx / ProductCard.css
```
