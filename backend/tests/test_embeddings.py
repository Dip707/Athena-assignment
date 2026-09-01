from types import SimpleNamespace

from app.data_loader import product_text
from app.models import Product
from app.search import embeddings
from app.search.embeddings import EmbeddingIndex


QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


class FakeVector(list):
    def tolist(self):
        return list(self)


class RecordingModel:
    def __init__(self):
        self.calls = []

    def encode(self, value, show_progress_bar=False):
        self.calls.append((value, show_progress_bar))
        if isinstance(value, list):
            return [FakeVector([float(index), 1.0]) for index, _ in enumerate(value)]
        return FakeVector([0.5, 0.5])


class FakeQdrantClient:
    def __init__(self, hits=None):
        self.hits = hits or []
        self.recreate_args = None
        self.upsert_args = None
        self.query_points_args = None

    def recreate_collection(self, **kwargs):
        self.recreate_args = kwargs

    def upsert(self, **kwargs):
        self.upsert_args = kwargs

    def query_points(self, **kwargs):
        self.query_points_args = kwargs
        return SimpleNamespace(points=self.hits)


class LegacyFakeQdrantClient:
    def __init__(self, hits=None):
        self.hits = hits or []
        self.search_args = None

    def search(self, **kwargs):
        self.search_args = kwargs
        return self.hits


def test_default_model_uses_bge_small_v15(monkeypatch):
    created = []
    model = RecordingModel()

    def make_model(name):
        created.append(name)
        return model

    monkeypatch.setattr(embeddings, "SentenceTransformer", make_model)

    EmbeddingIndex(client=FakeQdrantClient())

    assert created == ["BAAI/bge-small-en-v1.5"]


def test_build_encodes_product_documents_without_query_instruction():
    model = RecordingModel()
    client = FakeQdrantClient()
    products = [
        Product(
            id=7,
            title="Mechanical Keyboard",
            description="Clicky switches",
            category="Gaming",
            price=99,
        )
    ]

    EmbeddingIndex(client=client, model=model).build(products)

    assert model.calls[0] == ([product_text(products[0])], False)
    assert not model.calls[0][0][0].startswith(QUERY_INSTRUCTION)


def test_search_encodes_query_with_bge_retrieval_instruction():
    model = RecordingModel()
    client = FakeQdrantClient()
    index = EmbeddingIndex(client=client, model=model)

    index.search("quiet keyboard", top_k=3)

    assert model.calls == [(QUERY_INSTRUCTION + "quiet keyboard", False)]
    assert client.query_points_args["limit"] == 3
    assert client.query_points_args["query"] == [0.5, 0.5]


def test_search_returns_ranked_product_id_rank_score_tuples():
    model = RecordingModel()
    client = FakeQdrantClient(
        hits=[
            SimpleNamespace(payload={"product_id": 12}, score=0.92),
            SimpleNamespace(payload={"product_id": 4}, score=0.81),
        ]
    )
    index = EmbeddingIndex(client=client, model=model)

    assert index.search("headphones") == [
        (12, 1, 0.92),
        (4, 2, 0.81),
    ]


def test_search_supports_legacy_qdrant_client_search_api():
    model = RecordingModel()
    client = LegacyFakeQdrantClient(
        hits=[SimpleNamespace(payload={"product_id": 8}, score=0.75)]
    )
    index = EmbeddingIndex(client=client, model=model)

    assert index.search("controller") == [(8, 1, 0.75)]
    assert client.search_args["query_vector"] == [0.5, 0.5]
