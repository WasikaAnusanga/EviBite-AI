"""Lightweight Contract Stubs for Teammate Agents.

Member 1 owns Orchestration & Triage.
These stubs allow Member 1's Orchestrator to run end-to-end immediately,
leaving clear integration entry points for Members 2, 3, and 4.
"""

from typing import Any
from pydantic import BaseModel, Field


# ==========================================
# AGENT 2 CONTRACT STUB (Member 2 - Retrieval)
# ==========================================
class RetrievalRequest(BaseModel):
    trace_id: str
    query: str
    intent: str
    products: list[dict[str, Any]] = Field(default_factory=list)
    category: str | None = None
    requested_fields: list[str] = Field(default_factory=list)


class EvidenceObject(BaseModel):
    product_id: str
    name: str
    brand: str | None = None
    barcode: str | None = None
    categories: list[str] = Field(default_factory=list)
    ingredients_text: str | None = None
    allergens: list[str] = Field(default_factory=list)
    nutrition: dict[str, Any] = Field(default_factory=dict)
    completeness: float = 1.0
    source: str = "open_food_facts"


class RetrievalResponse(BaseModel):
    trace_id: str
    status: str = "FOUND"
    candidates: list[EvidenceObject] = Field(default_factory=list)


def stub_retrieval_service(request: RetrievalRequest) -> RetrievalResponse:
    """STUB FOR MEMBER 2: Product Information Retrieval Agent."""
    candidates = []
    for p in request.products:
        name = p.get("name") or "Packaged Product"
        candidates.append(
            EvidenceObject(
                product_id=f"off-{name.lower().replace(' ', '-')}",
                name=name,
                brand="Sample Brand",
                barcode=p.get("barcode") or "1234567890",
                categories=[request.category or "food"],
                ingredients_text="Sugar, cocoa, hazelnut, milk solids, lecithin.",
                allergens=["milk", "nuts", "hazelnut"],
                nutrition={"sugars_g_100g": 56.3, "protein_g_100g": 6.3, "energy_kcal_100g": 539},
                completeness=0.92,
            )
        )
    if not candidates:
        candidates.append(
            EvidenceObject(
                product_id="off-sample-item",
                name="Sample Packaged Food",
                brand="Generic Brand",
                barcode="0000000000000",
                categories=["packaged foods"],
                ingredients_text="Wheat flour, sugar, vegetable oil, salt.",
                allergens=["gluten"],
                nutrition={"sugars_g_100g": 12.0, "protein_g_100g": 4.5},
                completeness=0.85,
            )
        )
    return RetrievalResponse(trace_id=request.trace_id, status="FOUND", candidates=candidates)


# ==========================================
# AGENT 3 CONTRACT STUB (Member 3 - Analysis)
# ==========================================
class AnalysisRequest(BaseModel):
    trace_id: str
    primary_intent: str
    allergens: list[str] = Field(default_factory=list)
    nutrients: list[str] = Field(default_factory=list)
    dietary_requirements: list[str] = Field(default_factory=list)
    evidence: list[EvidenceObject] = Field(default_factory=list)
    original_query: str = ""


class AnalysisResponse(BaseModel):
    trace_id: str
    safety_status: str = "SUITABLE"  # SUITABLE, UNSUITABLE, UNCERTAIN
    risk_level: str = "LOW"
    findings: list[str] = Field(default_factory=list)
    uncertainty_reasons: list[str] = Field(default_factory=list)


def stub_analysis_service(request: AnalysisRequest) -> AnalysisResponse:
    """Delegates to Member 3's Nutrition & Allergen Analysis Agent service."""
    from backend.app.agents.nutrition_allergen.service import analysis_service
    return analysis_service(request)



# ==========================================
# AGENT 4 CONTRACT STUB (Member 4 - Response)
# ==========================================
class ResponseRequest(BaseModel):
    trace_id: str
    query: str
    intent: str
    triage_status: str
    evidence: list[EvidenceObject] = Field(default_factory=list)
    analysis: AnalysisResponse | None = None


class ResponseResponse(BaseModel):
    trace_id: str
    answer: str


def stub_response_service(request: ResponseRequest) -> ResponseResponse:
    """STUB FOR MEMBER 4: Recommendation & Response Agent."""
    if request.triage_status == "UNSUPPORTED":
        return ResponseResponse(
            trace_id=request.trace_id,
            answer="I am a supermarket product intelligence assistant for packaged foods. I cannot answer queries outside food product information.",
        )

    lines = []
    if request.analysis and request.analysis.findings:
        lines.extend(request.analysis.findings)
    elif request.evidence:
        for ev in request.evidence:
            lines.append(f"Product: {ev.name} (Brand: {ev.brand or 'N/A'}). Ingredients: {ev.ingredients_text or 'N/A'}.")
    else:
        lines.append("I checked the product information for your query.")

    answer_text = " ".join(lines)
    return ResponseResponse(trace_id=request.trace_id, answer=answer_text)
