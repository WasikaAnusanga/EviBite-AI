import pytest
from backend.app.sources.user_documents import UserDocumentSource, extract_structured_facts_from_text
from backend.app.services.document_service import save_user_document, delete_user_document
from backend.app.db.database import get_db

TEST_DOC_TEXT = """Product: Test Choco Bar

Ingredients:
Cocoa, sugar, milk powder, hazelnuts

Allergens:
Milk, Hazelnuts

Nutrition per 100g:
Sugar 32g
Protein 8g
Fat 21g
"""

@pytest.fixture
def setup_user_a_doc():
    user_id = "test_user_a_789"
    db = get_db()
    # Clean up previous test runs if any
    db.user_documents.delete_many({"user_id": user_id})
    db.document_chunks.delete_many({"user_id": user_id})

    doc = save_user_document(
        user_id=user_id,
        content_bytes=TEST_DOC_TEXT.encode("utf-8"),
        original_filename="Test_Choco_Bar_Spec.txt",
        content_type="text/plain",
    )
    yield user_id, doc.document_id

    # Teardown
    delete_user_document(user_id, doc.document_id)

def test_fact_extraction_from_text():
    facts = extract_structured_facts_from_text(TEST_DOC_TEXT)
    assert facts["product_name"] == "Test Choco Bar"
    assert "milk powder" in facts["ingredients_text"].lower()
    assert "milk" in facts["allergens"]
    assert "hazelnuts" in facts["allergens"]
    assert facts["nutrition"]["sugars_g_100g"] == 32.0
    assert facts["nutrition"]["protein_g_100g"] == 8.0
    assert facts["nutrition"]["fat_g_100g"] == 21.0

def test_retrieval_does_contain_milk(setup_user_a_doc):
    user_id, doc_id = setup_user_a_doc
    source = UserDocumentSource()
    ev_list = source.search_user_documents(
        user_id=user_id,
        query="Does Test Choco Bar contain milk?",
        triage_context={"products": [{"name": "Test Choco Bar"}], "allergens": ["milk"]},
    )
    assert len(ev_list) >= 1
    ev = ev_list[0]
    assert ev.source_type == "USER_DOCUMENT"
    assert ev.document_name == "Test_Choco_Bar_Spec.txt"
    assert ev.page_number == 1
    assert "milk powder" in ev.raw_text.lower()
    assert ev.relevance_score > 0.0

def test_retrieval_sugar_content(setup_user_a_doc):
    user_id, doc_id = setup_user_a_doc
    source = UserDocumentSource()
    ev_list = source.search_user_documents(
        user_id=user_id,
        query="How much sugar is in Test Choco Bar?",
        triage_context={"products": [{"name": "Test Choco Bar"}], "nutrients": ["sugar"]},
    )
    assert len(ev_list) >= 1
    ev = ev_list[0]
    assert ev.nutrition.get("sugars_g_100g") == 32.0

def test_retrieval_protein_content(setup_user_a_doc):
    user_id, doc_id = setup_user_a_doc
    source = UserDocumentSource()
    ev_list = source.search_user_documents(
        user_id=user_id,
        query="What is the protein content?",
        triage_context={"products": [{"name": "Test Choco Bar"}], "nutrients": ["protein"]},
    )
    assert len(ev_list) >= 1
    ev = ev_list[0]
    assert ev.nutrition.get("protein_g_100g") == 8.0

def test_unrelated_query_ranks_low(setup_user_a_doc):
    user_id, doc_id = setup_user_a_doc
    source = UserDocumentSource()
    ev_list = source.search_user_documents(
        user_id=user_id,
        query="Space shuttle orbital trajectory calculation",
    )
    assert len(ev_list) == 0

def test_user_a_doc_never_retrieved_by_user_b(setup_user_a_doc):
    user_a_id, doc_id = setup_user_a_doc
    user_b_id = "test_user_b_999"

    source = UserDocumentSource()

    # Query as User B -> MUST return 0 results
    ev_list_b = source.search_user_documents(
        user_id=user_b_id,
        query="Test Choco Bar milk sugar protein",
    )
    assert len(ev_list_b) == 0

def test_provenance_filename_and_page_survive(setup_user_a_doc):
    user_id, doc_id = setup_user_a_doc
    source = UserDocumentSource()
    ev_list = source.search_user_documents(
        user_id=user_id,
        query="Test Choco Bar ingredients",
    )
    assert len(ev_list) >= 1
    ev = ev_list[0]
    assert ev.document_name == "Test_Choco_Bar_Spec.txt"
    assert ev.page_number == 1
    assert ev.document_id == doc_id
