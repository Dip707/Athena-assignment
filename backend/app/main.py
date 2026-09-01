"""FastAPI application entrypoint for the AI Product Search Engine backend.

Wires together the hybrid search pipeline:
    1. BM25 lexical search (app.search.bm25).
    2. Semantic search via sentence-transformers + Qdrant (app.search.embeddings).
    3. Filter extraction (app.search.filters.extract_filters).
    4. Rank fusion (app.search.fusion.fuse_rankings).
    5. Soft-penalty filter application (app.search.filters.apply_filters).
    6. AI curation (app.search.curator.curate_results).
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import catalog_store
from app.data_loader import load_products
from app.models import Product, SearchResponse
from app.search.bm25 import bm25_search, init_bm25_index
from app.search.curator import curate_results
from app.search.embeddings import init_embedding_index, semantic_search
from app.search.filters import apply_filters, extract_filters
from app.search.fusion import fuse_rankings

logger = logging.getLogger("app")

# Number of candidates pulled from each retriever before fusion/pagination.
CANDIDATE_TOP_K = 50

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the product catalog. It's produced by a separate process and may
    # not exist yet — degrade gracefully rather than failing to start.
    try:
        products = load_products()
        logger.info("Loaded %d products from data/products.json", len(products))
    except FileNotFoundError as exc:
        logger.warning("%s Starting with an empty catalog.", exc)
        products = []

    catalog_store.set_current_products(products)

    # BM25 indexing is pure Python/NumPy — always safe to build, even empty.
    init_bm25_index(products)
    app.state.bm25_ready = True

    # Embedding indexing needs a local model download + a running Qdrant
    # instance. Don't let startup crash the whole app if either is
    # unavailable; /search will report 503 for the semantic leg instead.
    try:
        init_embedding_index(products)
        app.state.embeddings_ready = True
        logger.info("Embedding index ready (Qdrant + sentence-transformers).")
    except Exception:
        logger.exception(
            "Failed to initialize embedding index (is Qdrant running? "
            "was the sentence-transformers model reachable?). "
            "Semantic search will be unavailable until this is fixed."
        )
        app.state.embeddings_ready = False

    yield


app = FastAPI(title="AI Product Search Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/catalog/status")
def catalog_status() -> dict:
    """Report whether a non-empty catalog is ready for searching.

    The AI flag intentionally exposes only availability, never the configured
    credential itself, so the frontend can avoid an unnecessary second
    request when deterministic search is all that is available.
    """
    product_count = len(catalog_store.get_current_products())
    return {
        "loaded": product_count > 0,
        "product_count": product_count,
        "ai_enabled": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
    }


@app.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, description="Free-text search query."),
    page: int = Query(1, ge=1, description="1-indexed page number."),
    page_size: int = Query(10, ge=1, le=100, description="Results per page."),
    curate: bool = Query(
        True,
        description="Whether to apply AI curation and result tags.",
    ),
) -> SearchResponse:
    """Hybrid product search: BM25 + semantic retrieval, fused via weighted
    RRF, then soft-penalized by any extracted price/category filters. See
    app/search/fusion.py and app/search/filters.py for the algorithm.
    """
    if not getattr(app.state, "bm25_ready", False):
        raise HTTPException(status_code=503, detail="Search index not ready yet.")

    bm25_results = bm25_search(q, top_k=CANDIDATE_TOP_K)

    semantic_results: list[tuple[int, int, float]] = []
    if getattr(app.state, "embeddings_ready", False):
        try:
            semantic_results = semantic_search(q, top_k=CANDIDATE_TOP_K)
        except Exception:
            logger.exception("Semantic search failed for query=%r", q)
    else:
        logger.warning("Semantic index unavailable; proceeding with BM25 only.")

    fused = fuse_rankings(bm25_results, semantic_results)
    filters = extract_filters(q)
    results = apply_filters(fused, filters)
    if curate:
        results = curate_results(q, filters, results)

    total_results = len(results)
    start = (page - 1) * page_size
    page_results = results[start : start + page_size]

    return SearchResponse(
        query=q,
        results=page_results,
        applied_filters=filters,
        total_results=total_results,
        page=page,
        page_size=page_size,
    )


@app.post("/index")
def index_catalog(products: list[Product]) -> dict:
    """Replace the in-memory catalog and rebuild both search indices.

    Lets the deployed app be pointed at an arbitrary dataset at runtime
    instead of only the bundled data/products.json.
    """
    catalog_store.set_current_products(products)
    init_bm25_index(products)
    app.state.bm25_ready = True

    try:
        init_embedding_index(products)
        app.state.embeddings_ready = True
    except Exception:
        logger.exception("Failed to rebuild embedding index after /index upload.")
        app.state.embeddings_ready = False

    return {"indexed": len(products)}
