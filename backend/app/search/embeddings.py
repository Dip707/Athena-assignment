"""Semantic (dense embedding) search over the product catalog.

Uses a local sentence-transformers model (BAAI/bge-small-en-v1.5) to embed
product text at startup, upserts the vectors into a Qdrant collection
("products", cosine distance), and exposes `semantic_search` to embed a
query and run ANN search against that collection.

No external embedding API is used — everything runs locally, so no API
key is required. Qdrant itself is expected to be running locally (see
docker-compose.yml), reachable at QDRANT_HOST:QDRANT_PORT.
"""

from __future__ import annotations

import os

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer

from app.data_loader import product_text
from app.models import Product

MODEL_NAME = "BAAI/bge-small-en-v1.5"
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
COLLECTION_NAME = "products"

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))


class EmbeddingIndex:
    """Wraps the sentence-transformers model + Qdrant collection lifecycle."""

    def __init__(
        self,
        client: QdrantClient | None = None,
        model: SentenceTransformer | None = None,
    ) -> None:
        self.client = client or QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self.model = model or SentenceTransformer(MODEL_NAME)
        self.product_ids: list[int] = []

    def build(self, products: list[Product]) -> None:
        """Embed all products once and (re)populate the Qdrant collection."""
        self.product_ids = [p.id for p in products]
        if not products:
            return

        texts = [product_text(p) for p in products]
        vectors = self.model.encode(texts, show_progress_bar=False)
        vector_size = len(vectors[0])

        self.client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(
                size=vector_size,
                distance=qmodels.Distance.COSINE,
            ),
        )

        points = [
            qmodels.PointStruct(
                id=product.id,
                vector=vector.tolist(),
                payload={"product_id": product.id},
            )
            for product, vector in zip(products, vectors)
        ]
        self.client.upsert(collection_name=COLLECTION_NAME, points=points)

    def search(self, query: str, top_k: int = 10) -> list[tuple[int, int, float]]:
        """Embed `query` and return the top_k nearest products from Qdrant.

        Returns:
            A list of (product_id, rank, score) tuples, rank is 1-indexed,
            score is Qdrant's cosine similarity score (higher = closer).
        """
        query_vector = self.model.encode(
            QUERY_INSTRUCTION + query,
            show_progress_bar=False,
        ).tolist()
        query_points = getattr(self.client, "query_points", None)
        if callable(query_points):
            # qdrant-client 1.10+ consolidated vector search under
            # query_points() and wraps matches in QueryResponse.points.
            response = query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                limit=top_k,
            )
            hits = response.points
        else:
            # Retain compatibility with older qdrant-client releases and
            # simple test doubles that expose the former search() API.
            hits = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=top_k,
            )
        return [
            (hit.payload["product_id"], rank, float(hit.score))
            for rank, hit in enumerate(hits, start=1)
        ]


# Module-level singleton, populated at app startup via init_embedding_index().
_index: EmbeddingIndex | None = None


def init_embedding_index(products: list[Product]) -> EmbeddingIndex:
    """Load the model, build/populate the Qdrant collection. Call once at startup.

    Raises whatever the underlying SentenceTransformer/QdrantClient raise
    (e.g. connection errors if Qdrant isn't running, or download errors if
    the model can't be fetched) — callers should handle/log those explicitly
    rather than have this function swallow them silently.
    """
    global _index
    _index = EmbeddingIndex()
    _index.build(products)
    return _index


def semantic_search(query: str, top_k: int = 10) -> list[tuple[int, int, float]]:
    """Search the module-level embedding index.

    Raises:
        RuntimeError: If init_embedding_index() has not been called yet.
    """
    if _index is None:
        raise RuntimeError(
            "Embedding index not initialized. Call init_embedding_index(products) "
            "at app startup before searching."
        )
    return _index.search(query, top_k=top_k)
