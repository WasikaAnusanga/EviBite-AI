from uuid import uuid4
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field
from backend.app.models.triage import NutrientConstraint, Constraint

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
    user_id: str | None = None
    comparison_targets: list[str] = Field(default_factory=list)
    triage_context: dict[str, Any] = Field(default_factory=dict)


class EvidenceObject(BaseModel):
    evidence_id: str = Field(default_factory=lambda: f"ev-{uuid4().hex[:8]}")
    source_type: Literal["OPEN_FOOD_FACTS", "USER_DOCUMENT"] = "OPEN_FOOD_FACTS"
    source_name: str | None = "Open Food Facts"
    source_uri: str | None = None

    product_id: str | None = None
    barcode: str | None = None
    product_name: str | None = None
    name: str | None = None
    brand: str | None = None
    category: str | None = None
    categories: list[str] = Field(default_factory=list)

    ingredients_text: str | None = None
    allergens: list[str] = Field(default_factory=list)
    dietary_labels: list[str] = Field(default_factory=list)

    nutrition: dict[str, Any] = Field(default_factory=dict)
    raw_text: str | None = None

    document_id: str | None = None
    document_name: str | None = None
    page_number: int | None = None
    chunk_id: str | None = None

    relevance_score: float = 0.0
    completeness_score: float = 1.0
    completeness: float = 1.0
    combined_score: float = 0.0

    conflicting_evidence: bool = False
    field_provenance: dict[str, Any] = Field(default_factory=dict)
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def model_post_init(self, __context: Any) -> None:
        if self.product_name and not self.name:
            self.name = self.product_name
        elif self.name and not self.product_name:
            self.product_name = self.name
        if self.completeness != 1.0 and self.completeness_score == 1.0:
            self.completeness_score = self.completeness
        elif self.completeness_score != 1.0 and self.completeness == 1.0:
            self.completeness = self.completeness_score


class RetrievalResponse(BaseModel):
    trace_id: str
    status: Literal["FOUND", "PARTIAL", "NOT_FOUND", "ERROR"] = "FOUND"
    candidates: list[EvidenceObject] = Field(default_factory=list)
    searched_sources: list[str] = Field(default_factory=lambda: ["OPEN_FOOD_FACTS"])
    retry_count: int = 0
    original_query: str = ""
    reformulated_query: str | None = None

    @property
    def evidence(self) -> list[EvidenceObject]:
        return self.candidates


def stub_retrieval_service(request: RetrievalRequest) -> RetrievalResponse:
    """Delegates to Member 2's Product Information Retrieval Agent service."""
    from backend.app.agents.retrieval.service import retrieval_service
    return retrieval_service(request)



# ==========================================
# AGENT 3 CONTRACT STUB (Member 3 - Analysis)
# ==========================================
class AnalysisRequest(BaseModel):
    trace_id: str
    primary_intent: str
    allergens: list[str] = Field(default_factory=list)
    nutrients: list[str] = Field(default_factory=list)
    dietary_requirements: list[str] = Field(default_factory=list)
    nutrient_constraints: list[NutrientConstraint] = Field(default_factory=list)
    constraints: list[NutrientConstraint] = Field(default_factory=list)
    evidence: list[EvidenceObject] = Field(default_factory=list)
    original_query: str = ""


class AnalysisResponse(BaseModel):
    trace_id: str
    safety_status: str = "SUITABLE"  # SUITABLE, UNSUITABLE, INSUFFICIENT_EVIDENCE
    risk_level: str = "LOW"
    confidence: str = "high"
    allergen_findings: list[str] = Field(default_factory=list)
    dietary_findings: list[str] = Field(default_factory=list)
    nutrient_findings: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    uncertainty_reasons: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    conflicting_evidence: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def verdict(self) -> str:
        return self.safety_status


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
    nutrient_constraints: list[NutrientConstraint] = Field(default_factory=list)
    constraints: list[NutrientConstraint] = Field(default_factory=list)
    preferences: dict[str, bool] = Field(default_factory=dict)
    nutrients: list[str] = Field(default_factory=list)

class ResponseResponse(BaseModel):
    trace_id: str
    answer: str
    status: str = "OK"
    warnings: list[str] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    ranked_products: list[dict[str, Any]] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


def stub_response_service(request: ResponseRequest) -> ResponseResponse:
    from backend.app.agents.recommendation_response.service import response_service
    return response_service(request)

