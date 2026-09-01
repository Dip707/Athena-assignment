import pytest

from app.models import Product
from app.search import curator


FIXTURE_CANDIDATES = [
    {"product": Product(id=1, title="Mechanical Keyboard", description="", category="Gaming Keyboards", price=3999), "fused_score": 0.5, "explanation": {}},
    {"product": Product(id=2, title="Premium Keyboard", description="", category="Gaming Keyboards", price=5200), "fused_score": 0.4, "explanation": {}},
    {"product": Product(id=3, title="Gaming Chair", description="", category="Gaming Chairs", price=9999), "fused_score": 0.3, "explanation": {}},
]

FILTERS = {"price_max": 5000.0, "category_hint": "Gaming Keyboards"}


class _FakeFunctionCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args


class _FakePart:
    def __init__(self, function_call):
        self.function_call = function_call


class _FakeContent:
    def __init__(self, parts):
        self.parts = parts


class _FakeCandidate:
    def __init__(self, content):
        self.content = content


class _FakeResponse:
    def __init__(self, picks):
        function_call = _FakeFunctionCall("select_curated_results", {"picks": picks})
        self.candidates = [_FakeCandidate(_FakeContent([_FakePart(function_call)]))]


def _fake_client_returning(response):
    class _FakeModels:
        def generate_content(self, **kwargs):
            return response

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            self.models = _FakeModels()

    return _FakeClient


def test_curate_results_skips_when_no_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = curator.curate_results("mechanical keyboard", FILTERS, FIXTURE_CANDIDATES)
    assert result == FIXTURE_CANDIDATES


def test_curate_results_applies_valid_picks(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    fake_response = _FakeResponse(
        picks=[
            {"slot": "best_match", "product_id": 1},
            {"slot": "best_near_price", "product_id": 2},
            {"slot": "best_outside_both", "product_id": 3},
        ]
    )
    monkeypatch.setattr(curator.genai, "Client", _fake_client_returning(fake_response))

    result = curator.curate_results("mechanical keyboard under 5000", FILTERS, FIXTURE_CANDIDATES)

    assert [r["product"].id for r in result[:3]] == [1, 2, 3]
    assert result[0]["tag"] == "Best match"
    assert result[1]["tag"] == "Just above your budget"
    assert result[2]["tag"] == "Outside your category and budget"


def test_curate_results_drops_picks_that_dont_match_the_claimed_slot(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    # product 1 IS in the category hint, so a "best_outside_category" claim
    # about it is false and must be dropped rather than trusted.
    fake_response = _FakeResponse(
        picks=[
            {"slot": "best_match", "product_id": 1},
            {"slot": "best_outside_category", "product_id": 1},
        ]
    )
    monkeypatch.setattr(curator.genai, "Client", _fake_client_returning(fake_response))

    result = curator.curate_results("mechanical keyboard", FILTERS, FIXTURE_CANDIDATES)

    assert result == FIXTURE_CANDIDATES


def test_curate_results_falls_back_on_api_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    class _FailingModels:
        def generate_content(self, **kwargs):
            raise RuntimeError("simulated API failure")

    class _FailingClient:
        def __init__(self, *args, **kwargs):
            self.models = _FailingModels()

    monkeypatch.setattr(curator.genai, "Client", _FailingClient)

    result = curator.curate_results("mechanical keyboard", FILTERS, FIXTURE_CANDIDATES)
    assert result == FIXTURE_CANDIDATES


def test_curate_results_forces_one_allowed_function_call(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    captured = {}

    class _Models:
        def generate_content(self, **kwargs):
            captured.update(kwargs)
            return _FakeResponse([{"slot": "best_match", "product_id": 1}])

    class _Client:
        def __init__(self, *args, **kwargs):
            self.models = _Models()

    monkeypatch.setattr(curator.genai, "Client", _Client)
    curator.curate_results("mechanical keyboard", FILTERS, FIXTURE_CANDIDATES)

    assert captured["model"] == curator.MODEL_NAME
    config = captured["config"]
    function_config = config.tool_config.function_calling_config
    assert function_config.mode.value == "ANY"
    assert function_config.allowed_function_names == ["select_curated_results"]
    assert config.http_options.timeout == 10000


def test_curate_results_falls_back_when_best_match_is_missing(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    fake_response = _FakeResponse(
        picks=[{"slot": "best_near_price", "product_id": 2}]
    )
    monkeypatch.setattr(curator.genai, "Client", _fake_client_returning(fake_response))

    result = curator.curate_results("mechanical keyboard under 5000", FILTERS, FIXTURE_CANDIDATES)

    assert result == FIXTURE_CANDIDATES


def test_curate_results_falls_back_on_mixed_valid_and_malformed_picks(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    fake_response = _FakeResponse(
        picks=[
            {"slot": "best_match", "product_id": 1},
            {"slot": "best_near_price", "product_id": "2"},
        ]
    )
    monkeypatch.setattr(curator.genai, "Client", _fake_client_returning(fake_response))

    result = curator.curate_results("mechanical keyboard under 5000", FILTERS, FIXTURE_CANDIDATES)

    assert result == FIXTURE_CANDIDATES


def test_curate_results_falls_back_on_unknown_product_id(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    fake_response = _FakeResponse(
        picks=[
            {"slot": "best_match", "product_id": 1},
            {"slot": "best_near_price", "product_id": 999},
        ]
    )
    monkeypatch.setattr(curator.genai, "Client", _fake_client_returning(fake_response))

    result = curator.curate_results("mechanical keyboard under 5000", FILTERS, FIXTURE_CANDIDATES)

    assert result == FIXTURE_CANDIDATES


def test_curate_results_falls_back_on_non_integer_product_id(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    fake_response = _FakeResponse(
        picks=[
            {"slot": "best_match", "product_id": 1},
            {"slot": "best_near_price", "product_id": "2"},
        ]
    )
    monkeypatch.setattr(curator.genai, "Client", _fake_client_returning(fake_response))

    result = curator.curate_results("mechanical keyboard under 5000", FILTERS, FIXTURE_CANDIDATES)

    assert result == FIXTURE_CANDIDATES


def test_curate_results_falls_back_on_duplicate_slots(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    fake_response = _FakeResponse(
        picks=[
            {"slot": "best_match", "product_id": 1},
            {"slot": "best_match", "product_id": 2},
        ]
    )
    monkeypatch.setattr(curator.genai, "Client", _fake_client_returning(fake_response))

    result = curator.curate_results("mechanical keyboard", FILTERS, FIXTURE_CANDIDATES)

    assert result == FIXTURE_CANDIDATES


def test_curate_results_falls_back_on_duplicate_product_ids(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    fake_response = _FakeResponse(
        picks=[
            {"slot": "best_match", "product_id": 1},
            {"slot": "best_near_price", "product_id": 1},
        ]
    )
    monkeypatch.setattr(curator.genai, "Client", _fake_client_returning(fake_response))

    result = curator.curate_results("mechanical keyboard under 5000", FILTERS, FIXTURE_CANDIDATES)

    assert result == FIXTURE_CANDIDATES
