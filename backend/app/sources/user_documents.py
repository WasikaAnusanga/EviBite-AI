import re
import logging
from typing import Any
from rank_bm25 import BM25Okapi

from backend.app.agents.agent_stubs import EvidenceObject
from backend.app.sources.base import ProductSource
from backend.app.db.database import get_db

logger = logging.getLogger(__name__)

_user_index_cache: dict[str, tuple[BM25Okapi, list[dict[str, Any]]]] = {}


def invalidate_user_index(user_id: str) -> None:
    """Invalidate cached in-memory BM25 index for a specific user."""
    if user_id in _user_index_cache:
        del _user_index_cache[user_id]


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return [w for w in re.findall(r"\w+", text.lower()) if len(w) > 1]


def extract_structured_facts_from_text(raw_text: str) -> dict[str, Any]:
    """Extract explicit product facts from raw document text.
    
    DOES NOT hallucinate fields. Unfound fields remain None or empty lists.
    """
    facts: dict[str, Any] = {
        "product_name": None,
        "ingredients_text": None,
        "allergens": [],
        "nutrition": {},
    }

    # Extract Product Name: e.g. "Product: Test Choco Bar" or "Product Name: ..."
    prod_match = re.search(r"(?:Product|Product Name|Item):\s*([^\n\r]+)", raw_text, re.IGNORECASE)
    if prod_match:
        facts["product_name"] = prod_match.group(1).strip()

    # Extract Ingredients: e.g. "Ingredients:\nCocoa, sugar, milk powder"
    ing_match = re.search(r"Ingredients:\s*([^\n\r]+(?:\n[^\n\r]+)*?)(?=\n\n|\n[A-Z][a-z]+:|\Z)", raw_text, re.IGNORECASE)
    if ing_match:
        facts["ingredients_text"] = ing_match.group(1).strip().replace("\n", ", ")

    # Extract Allergens: e.g. "Allergens:\nMilk, Hazelnuts"
    alg_match = re.search(r"Allergens:\s*([^\n\r]+(?:\n[^\n\r]+)*?)(?=\n\n|\n[A-Z][a-z]+:|\Z)", raw_text, re.IGNORECASE)
    if alg_match:
        raw_algs = alg_match.group(1).strip()
        algs = [a.strip().lower() for a in re.split(r"[,;\n]+", raw_algs) if a.strip()]
        facts["allergens"] = algs

    # Extract Nutrition: e.g. "Sugar 32g", "Protein 8g", "Fat 21g", "Sodium 100mg", "Calories 450"
    nutrition = {}
    sugar_m = re.search(r"Sugar[s]?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g", raw_text, re.IGNORECASE)
    if sugar_m:
        nutrition["sugars_g_100g"] = float(sugar_m.group(1))

    protein_m = re.search(r"Protein[s]?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g", raw_text, re.IGNORECASE)
    if protein_m:
        nutrition["protein_g_100g"] = float(protein_m.group(1))

    fat_m = re.search(r"Fat[s]?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g", raw_text, re.IGNORECASE)
    if fat_m:
        nutrition["fat_g_100g"] = float(fat_m.group(1))

    sat_fat_m = re.search(r"Saturated\s+Fat\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*g", raw_text, re.IGNORECASE)
    if sat_fat_m:
        nutrition["saturated_fat_g_100g"] = float(sat_fat_m.group(1))

    energy_m = re.search(r"(?:Calories|Energy)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:kcal|cal)?", raw_text, re.IGNORECASE)
    if energy_m:
        nutrition["energy_kcal_100g"] = float(energy_m.group(1))

    sodium_m = re.search(r"Sodium\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*mg", raw_text, re.IGNORECASE)
    if sodium_m:
        nutrition["sodium_mg_100g"] = float(sodium_m.group(1))

    facts["nutrition"] = nutrition
    return facts


class UserDocumentSource(ProductSource):
    """ProductSource adapter for searching authenticated personal user documents using BM25."""

    def __init__(self, user_id: str | None = None):
        self.user_id = user_id

    def _get_bm25_index_for_user(self, user_id: str) -> tuple[BM25Okapi | None, list[dict[str, Any]]]:
        if user_id in _user_index_cache:
            return _user_index_cache[user_id]

        db = get_db()
        # Strictly filter by user_id to guarantee user index isolation
        cursor = db.document_chunks.find({"user_id": user_id})
        chunks = list(cursor)

        if not chunks:
            return None, []

        corpus = [_tokenize(c["text"]) for c in chunks]
        bm25 = BM25Okapi(corpus)
        # Ensure non-negative IDF for small corpora / single-document collections
        for word, idf in list(bm25.idf.items()):
            if idf <= 0:
                bm25.idf[word] = 0.1

        _user_index_cache[user_id] = (bm25, chunks)
        return bm25, chunks

    def search_user_documents(
        self,
        user_id: str,
        query: str,
        triage_context: dict[str, Any] | None = None,
        limit: int = 5,
    ) -> list[EvidenceObject]:
        """Search user document collection using BM25 over isolated user chunks.
        
        Builds an effective search query incorporating raw user query + extracted entities.
        """
        if not user_id:
            return []

        # 1. Build Effective Search Query
        effective_query_parts = [query]
        if triage_context:
            for p in triage_context.get("products", []):
                p_name = p.get("name") if isinstance(p, dict) else getattr(p, "name", None)
                if p_name:
                    effective_query_parts.append(str(p_name))
            if triage_context.get("brand"):
                effective_query_parts.append(str(triage_context["brand"]))
            if triage_context.get("category"):
                effective_query_parts.append(str(triage_context["category"]))
            effective_query_parts.extend(triage_context.get("allergens", []))
            effective_query_parts.extend(triage_context.get("dietary_requirements", []))
            effective_query_parts.extend(triage_context.get("nutrients", []))

        effective_query_str = " ".join(effective_query_parts)
        query_tokens = _tokenize(effective_query_str)
        if not query_tokens:
            return []

        # 2. Get User Isolated Index
        bm25, chunks = self._get_bm25_index_for_user(user_id)
        if not bm25 or not chunks:
            return []

        # 3. BM25 Scoring
        scores = bm25.get_scores(query_tokens)

        # Pair chunks with scores
        scored_chunks = []
        for chunk, score in zip(chunks, scores):
            if score > 0.001:  # Relevance threshold check
                scored_chunks.append((score, chunk))

        # Sort descending by BM25 score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored_chunks[:limit]

        # 4. Convert to EvidenceObject
        results: list[EvidenceObject] = []
        for score, chunk in top_chunks:
            raw_text = chunk["text"]
            meta = chunk.get("metadata", {})
            filename = meta.get("filename") or "User Document"
            doc_id = chunk["document_id"]
            page_num = chunk.get("page_number", 1)

            # Deterministic fact extraction
            facts = extract_structured_facts_from_text(raw_text)

            ev = EvidenceObject(
                evidence_id=f"doc-{chunk['_id']}",
                source_type="USER_DOCUMENT",
                source_name=filename,
                source_uri=f"user_documents/{user_id}/{doc_id}",
                product_id=doc_id,
                product_name=facts["product_name"] or filename,
                name=facts["product_name"] or filename,
                ingredients_text=facts["ingredients_text"],
                allergens=facts["allergens"],
                nutrition=facts["nutrition"],
                raw_text=raw_text,
                document_id=doc_id,
                document_name=filename,
                page_number=page_num,
                chunk_id=str(chunk["_id"]),
                relevance_score=round(float(score), 4),
                completeness=1.0 if facts["ingredients_text"] or facts["nutrition"] else 0.7,
            )
            results.append(ev)

        return results

    def get_by_barcode(self, barcode: str) -> EvidenceObject | None:
        """User documents don't index barcodes directly by default."""
        return None

    def search(
        self,
        query: str,
        category: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[EvidenceObject]:
        user_id = (filters or {}).get("user_id") or self.user_id
        if not user_id:
            return []
        return self.search_user_documents(user_id=user_id, query=query, limit=limit)
