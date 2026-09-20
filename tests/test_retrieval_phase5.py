import time
import pytest
from unittest.mock import MagicMock

from backend.app.agents.agent_stubs import EvidenceObject, RetrievalRequest
from backend.app.agents.retrieval.service import retrieval_service
from backend.app.sources.base import ProductSource
from backend.app.sources.user_documents import UserDocumentSource, invalidate_user_index
from backend.app.services.document_service import save_user_document, delete_user_document
from backend.app.db.database import get_db


class MockOFFSource(ProductSource):
    """Mock OpenFoodFacts source for deterministic testing."""

    def __init__(self, barcode_map=None, search_map=None, should_fail=False):
        self.barcode_map = barcode_map or {}
        self.search_map = search_map or {}
        self.should_fail = should_fail

    def get_by_barcode(self, barcode: str) -> EvidenceObject | None:
        if self.should_fail:
            raise TimeoutError("OFF API Connection Timeout")
        return self.barcode_map.get(barcode)

    def search(
        self,
        query: str,
        category: str | None = None,
        filters: dict | None = None,
        limit: int = 10,
    ) -> list[EvidenceObject]:
        if self.should_fail:
            raise TimeoutError("OFF API Connection Timeout")
        return self.search_map.get(query.lower(), [])


@pytest.fixture
def setup_user_docs():
    user1_id = "phase5_user_alpha"
    user2_id = "phase5_user_beta"

    db = get_db()
    db.user_documents.delete_many({"user_id": {"$in": [user1_id, user2_id]}})
    db.document_chunks.delete_many({"user_id": {"$in": [user1_id, user2_id]}})

    doc1_content = """Product: Test Choco Bar

Ingredients:
Cocoa, sugar, milk powder, hazelnuts

Allergens:
Milk, Hazelnuts

Nutrition per 100g:
Sugar 32g
Protein 8g
Fat 21g
"""
    doc1 = save_user_document(
        user_id=user1_id,
        content_bytes=doc1_content.encode("utf-8"),
        original_filename="Supplier_Allergen_Spec.txt",
        content_type="text/plain",
    )

    yield user1_id, user2_id, doc1.document_id

    delete_user_document(user1_id, doc1.document_id)
    invalidate_user_index(user1_id)
    invalidate_user_index(user2_id)


def test_off_only_retrieval():
    off_mock = MockOFFSource(
        search_map={
            "nutella": [
                EvidenceObject(
                    product_id="off-123",
                    name="Nutella Hazelnut Spread",
                    brand="Ferrero",
                    ingredients_text="Sugar, palm oil, hazelnuts, milk, cocoa.",
                    allergens=["milk", "hazelnuts"],
                    source_type="OPEN_FOOD_FACTS",
                )
            ]
        }
    )

    req = RetrievalRequest(
        trace_id="t-1",
        query="nutella",
        intent="PRODUCT_SEARCH",
        user_id=None,
    )

    res = retrieval_service(req, source=off_mock)
    assert res.status == "FOUND"
    assert "OPEN_FOOD_FACTS" in res.searched_sources
    assert len(res.candidates) >= 1
    assert res.candidates[0].name == "Nutella Hazelnut Spread"


def test_user_document_only_retrieval(setup_user_docs):
    user1_id, user2_id, doc_id = setup_user_docs
    off_mock = MockOFFSource(search_map={})

    req = RetrievalRequest(
        trace_id="t-2",
        query="Test Choco Bar milk",
        intent="ALLERGEN_CHECK",
        user_id=user1_id,
    )

    res = retrieval_service(req, source=off_mock)
    assert res.status == "FOUND"
    assert "USER_DOCUMENT" in res.searched_sources
    assert len(res.candidates) >= 1
    assert res.candidates[0].source_type == "USER_DOCUMENT"
    assert res.candidates[0].document_name == "Supplier_Allergen_Spec.txt"


def test_both_sources_combined(setup_user_docs):
    user1_id, user2_id, doc_id = setup_user_docs

    off_mock = MockOFFSource(
        search_map={
            "test choco bar": [
                EvidenceObject(
                    product_id="off-choco-1",
                    name="Test Choco Bar",
                    brand="Store Brand",
                    ingredients_text="Cocoa, sugar, palm oil.",
                    allergens=["soy"],
                    source_type="OPEN_FOOD_FACTS",
                )
            ]
        }
    )

    req = RetrievalRequest(
        trace_id="t-3",
        query="Test Choco Bar",
        intent="PRODUCT_SEARCH",
        products=[{"name": "Test Choco Bar"}],
        user_id=user1_id,
    )

    res = retrieval_service(req, source=off_mock)
    assert res.status == "FOUND"
    source_types = [c.source_type for c in res.candidates]
    assert "OPEN_FOOD_FACTS" in source_types
    assert "USER_DOCUMENT" in source_types


def test_off_timeout_document_survives(setup_user_docs):
    user1_id, user2_id, doc_id = setup_user_docs
    off_mock = MockOFFSource(should_fail=True)

    req = RetrievalRequest(
        trace_id="t-4",
        query="Test Choco Bar sugar content",
        intent="NUTRITION_QUERY",
        user_id=user1_id,
    )

    res = retrieval_service(req, source=off_mock)
    assert res.status == "FOUND"
    assert len(res.candidates) >= 1
    assert res.candidates[0].source_type == "USER_DOCUMENT"
    assert res.candidates[0].nutrition.get("sugars_g_100g") == 32.0


def test_document_error_off_survives():
    off_mock = MockOFFSource(
        search_map={
            "cheerios": [
                EvidenceObject(
                    product_id="off-cheerios",
                    name="Cheerios Cereal",
                    source_type="OPEN_FOOD_FACTS",
                )
            ]
        }
    )
    doc_mock = MagicMock()
    doc_mock.search_user_documents.side_effect = RuntimeError("Database offline")

    req = RetrievalRequest(
        trace_id="t-5",
        query="cheerios",
        intent="PRODUCT_SEARCH",
        user_id="user_error_test",
    )

    res = retrieval_service(req, source=off_mock, doc_source=doc_mock)
    assert res.status == "FOUND"
    assert len(res.candidates) >= 1
    assert res.candidates[0].name == "Cheerios Cereal"


def test_not_found_status():
    off_mock = MockOFFSource(search_map={})
    req = RetrievalRequest(
        trace_id="t-6",
        query="nonexistent_unregistered_food_item_xyz_99",
        intent="PRODUCT_SEARCH",
        user_id=None,
    )

    res = retrieval_service(req, source=off_mock)
    assert res.status == "NOT_FOUND"
    assert len(res.candidates) == 0


def test_conflicting_sources_flagged(setup_user_docs):
    user1_id, user2_id, doc_id = setup_user_docs

    # OFF item claims product has Soy allergen, document claims Milk and Hazelnuts
    off_mock = MockOFFSource(
        search_map={
            "test choco bar": [
                EvidenceObject(
                    product_id="off-choco-bar",
                    name="Test Choco Bar",
                    brand="Test Choco Bar",
                    ingredients_text="Cocoa, soy lecithin.",
                    allergens=["soy"],
                    source_type="OPEN_FOOD_FACTS",
                )
            ]
        }
    )

    req = RetrievalRequest(
        trace_id="t-7",
        query="Test Choco Bar",
        intent="ALLERGEN_CHECK",
        products=[{"name": "Test Choco Bar"}],
        user_id=user1_id,
    )

    res = retrieval_service(req, source=off_mock)
    assert len(res.candidates) >= 2
    conflicting_candidates = [c for c in res.candidates if c.conflicting_evidence]
    assert len(conflicting_candidates) >= 2


def test_exact_barcode_retrieval():
    off_mock = MockOFFSource(
        barcode_map={
            "3017620422003": EvidenceObject(
                product_id="off-nutella",
                barcode="3017620422003",
                name="Nutella",
                source_type="OPEN_FOOD_FACTS",
            )
        }
    )

    req = RetrievalRequest(
        trace_id="t-8",
        query="3017620422003",
        intent="BARCODE_LOOKUP",
    )

    res = retrieval_service(req, source=off_mock)
    assert res.status == "FOUND"
    assert res.candidates[0].barcode == "3017620422003"


def test_bounded_retry_max_one():
    off_mock = MockOFFSource(
        search_map={
            "oats": [
                EvidenceObject(
                    product_id="off-oats",
                    name="Rolled Oats",
                    source_type="OPEN_FOOD_FACTS",
                )
            ]
        }
    )

    # Initial query has stopwords "low sugar high protein oats"
    req = RetrievalRequest(
        trace_id="t-9",
        query="low sugar high protein oats",
        intent="PRODUCT_SEARCH",
        user_id=None,
    )

    res = retrieval_service(req, source=off_mock)
    assert res.retry_count <= 1
    assert res.status == "FOUND"


def test_user_isolation(setup_user_docs):
    user1_id, user2_id, doc_id = setup_user_docs
    off_mock = MockOFFSource(search_map={})

    req_b = RetrievalRequest(
        trace_id="t-10",
        query="Test Choco Bar milk sugar protein",
        intent="PRODUCT_SEARCH",
        user_id=user2_id,  # User 2 has 0 documents
    )

    res_b = retrieval_service(req_b, source=off_mock)
    assert res_b.status == "NOT_FOUND"
    assert len(res_b.candidates) == 0


def test_provenance_information(setup_user_docs):
    user1_id, user2_id, doc_id = setup_user_docs
    off_mock = MockOFFSource(search_map={})

    req = RetrievalRequest(
        trace_id="t-11",
        query="Test Choco Bar",
        intent="PRODUCT_SEARCH",
        user_id=user1_id,
    )

    res = retrieval_service(req, source=off_mock)
    doc_ev = res.candidates[0]
    assert doc_ev.document_id == doc_id
    assert doc_ev.document_name == "Supplier_Allergen_Spec.txt"
    assert doc_ev.page_number == 1
    assert doc_ev.chunk_id is not None


def test_retrieval_latency():
    off_mock = MockOFFSource(search_map={})
    req = RetrievalRequest(
        trace_id="t-12",
        query="quick search query test",
        intent="PRODUCT_SEARCH",
        user_id=None,
    )

    start_time = time.perf_counter()
    res = retrieval_service(req, source=off_mock)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    assert elapsed_ms < 500  # Must return under 500ms
