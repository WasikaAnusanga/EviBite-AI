"""Unit and Integration Tests for Member 2 Product Information Retrieval Agent."""

import pytest
from backend.app.agents.agent_stubs import EvidenceObject, RetrievalRequest
from backend.app.agents.retrieval.service import (
    _calculate_query_completeness,
    _extract_barcode,
    _normalize_text,
    _rank_and_score_candidates,
    _reformulate_query,
    retrieval_service,
)
from backend.app.models.messages import ChatRequest
from backend.app.orchestration.orchestrator import run_orchestration
from backend.app.sources.base import ProductSource
from backend.app.sources.open_food_facts import OpenFoodFactsSource


class MockProductSource(ProductSource):
    """Mock ProductSource implementation for fast deterministic unit tests."""

    def __init__(self):
        self.products = [
            EvidenceObject(
                product_id="off-3017620422003",
                name="Nutella Hazelnut Spread",
                brand="Ferrero",
                barcode="3017620422003",
                categories=["spreads", "hazelnut spreads"],
                ingredients_text="Sugar, palm oil, hazelnuts (13%), skimmed milk powder (8.7%), fat-reduced cocoa (7.4%), emulsifier: lecithins (soy), vanillin.",
                allergens=["hazelnut", "milk", "soy"],
                nutrition={"sugars_g_100g": 56.3, "protein_g_100g": 6.3, "fat_g_100g": 30.9, "energy_kcal_100g": 539.0},
                completeness=0.95,
                source="open_food_facts",
            ),
            EvidenceObject(
                product_id="off-7613035654321",
                name="Cheerios Honey & Oats Cereal",
                brand="Nestle",
                barcode="7613035654321",
                categories=["cereals", "breakfasts"],
                ingredients_text="Whole grain oat flour, sugar, oat bran, honey, salt.",
                allergens=["oats"],
                nutrition={"sugars_g_100g": 9.3, "protein_g_100g": 8.4, "fat_g_100g": 3.8, "energy_kcal_100g": 382.0},
                completeness=0.90,
                source="open_food_facts",
            ),
        ]

    def get_by_barcode(self, barcode: str) -> EvidenceObject | None:
        for p in self.products:
            if p.barcode == barcode:
                return p
        return None

    def search(self, query: str, category: str | None = None, filters=None, limit: int = 10) -> list[EvidenceObject]:
        q_lower = query.lower()
        results = [p for p in self.products if any(w in p.name.lower() or w in (p.brand or "").lower() for w in q_lower.split())]
        return results or self.products[:limit]


def test_product_source_abstraction():
    source = MockProductSource()
    bc_result = source.get_by_barcode("3017620422003")
    assert bc_result is not None
    assert bc_result.name == "Nutella Hazelnut Spread"

    search_results = source.search("Cheerios")
    assert len(search_results) >= 1
    assert search_results[0].brand == "Nestle"


def test_open_food_facts_normalization_and_completeness():
    off_source = OpenFoodFactsSource()
    raw_sample = {
        "code": "5000167032104",
        "product_name": "Special K Original",
        "brands": "Kellogg's",
        "categories_tags": ["en:cereals", "en:breakfasts"],
        "ingredients_text": "Rice, wheat gluten, sugar, barley malt extract, salt.",
        "allergens_tags": ["en:gluten", "en:wheat"],
        "nutriments": {
            "sugars_100g": 14.0,
            "proteins_100g": 14.0,
            "fat_100g": 1.5,
            "energy-kcal_100g": 375.0,
            "sodium_100g": 0.35,
        },
    }
    ev = off_source._normalize_product(raw_sample)
    assert ev.product_id == "off-5000167032104"
    assert ev.name == "Special K Original"
    assert ev.brand == "Kellogg's"
    assert "gluten" in ev.allergens
    assert ev.nutrition.get("sugars_g_100g") == 14.0
    assert ev.completeness >= 0.85


def test_query_normalization_and_extraction():
    assert _normalize_text("  Low-Sugar  Cereal!! ") == "low sugar cereal"
    req = RetrievalRequest(
        trace_id="REQ-TEST",
        query="Check barcode 3017620422003",
        intent="barcode_lookup",
        products=[{"name": "Nutella", "barcode": "3017620422003"}],
    )
    assert _extract_barcode(req) == "3017620422003"


def test_query_reformulation():
    reformulated = _reformulate_query("low sugar healthy breakfast cereal")
    assert "cereal" in reformulated
    assert "low" not in reformulated.split()
    assert "healthy" not in reformulated.split()


def test_completeness_scoring_and_ranking():
    ev1 = EvidenceObject(
        product_id="p1",
        name="High Completeness Cereal",
        brand="Brand A",
        barcode="1111",
        categories=["cereal"],
        ingredients_text="Oats, wheat, sugar, salt",
        allergens=["gluten"],
        nutrition={"sugars_g_100g": 5.0, "protein_g_100g": 10.0},
        completeness=0.9,
    )
    ev2 = EvidenceObject(
        product_id="p2",
        name="Low Completeness Cereal",
        brand="Brand B",
        barcode="2222",
        categories=["cereal"],
        ingredients_text=None,
        allergens=[],
        nutrition={},
        completeness=0.3,
    )
    req = RetrievalRequest(
        trace_id="REQ-RANK",
        query="cereal",
        intent="product_search",
        requested_fields=["sugars", "ingredients", "allergens"],
    )
    ranked = _rank_and_score_candidates([ev2, ev1], req)
    assert ranked[0].product_id == "p1"
    assert ranked[0].completeness > ranked[1].completeness


def test_retrieval_service_with_mock_source():
    mock_source = MockProductSource()
    req = RetrievalRequest(
        trace_id="REQ-1234",
        query="Nutella",
        intent="product_search",
        products=[{"name": "Nutella"}],
        requested_fields=["allergens", "sugars"],
    )
    res = retrieval_service(req, source=mock_source)
    assert res.status == "FOUND"
    assert len(res.candidates) >= 1
    assert res.candidates[0].name == "Nutella Hazelnut Spread"
    assert "hazelnut" in res.candidates[0].allergens


def test_retrieval_service_fallback_fixtures():
    # Query with no match using mock source returning empty list
    class EmptySource(ProductSource):
        def get_by_barcode(self, barcode: str):
            return None
        def search(self, query, category=None, filters=None, limit=10):
            return []

    req = RetrievalRequest(
        trace_id="REQ-FALLBACK",
        query="unknown snack product",
        intent="product_search",
        category="snack",
    )
    res = retrieval_service(req, source=EmptySource())
    assert res.status in ("FOUND", "PARTIAL")
    assert len(res.candidates) > 0


def test_orchestrator_integration_with_retrieval():
    chat_req = ChatRequest(message="Tell me about Nutella and its allergens")
    response = run_orchestration(chat_req)
    assert response.trace_id.startswith("REQ-")
    assert "retrieval" in response.execution_path
    retrieval_step = next(s for s in response.execution_steps if s.agent == "retrieval")
    assert retrieval_step.status in ("FOUND", "PARTIAL")
