from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Intent(str, Enum):
    PRODUCT_SEARCH = "product_search"
    BARCODE_LOOKUP = "barcode_lookup"
    ALLERGEN_QUERY = "allergen_query"
    NUTRITION_QUERY = "nutrition_query"
    COMPARISON = "comparison"
    DIETARY_QUERY = "dietary_query"
    RECOMMENDATION = "recommendation"
    UNKNOWN = "unknown"


class InputType(str, Enum):
    NATURAL_LANGUAGE = "natural_language"
    BARCODE = "barcode"
    FOLLOW_UP = "follow_up"


class TriageStatus(str, Enum):
    READY = "READY"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RouteAgent(str, Enum):
    RETRIEVAL = "retrieval"
    ANALYSIS = "analysis"
    RESPONSE = "response"


class ProductEntity(BaseModel):
    name: str | None = None
    brand: str | None = None
    barcode: str | None = None


class Constraint(BaseModel):
    field: str
    operator: Literal["<", "<=", "=", ">=", ">"]
    value: float
    unit: str | None = None


class Comparison(BaseModel):
    metric: str | None = None
    goal: Literal["lower", "higher", "equal", "best"] | None = None


class Clarification(BaseModel):
    required: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    question: str | None = None


class RoutingDecision(BaseModel):
    next_agent: RouteAgent | None = None
    required_agents: list[RouteAgent] = Field(default_factory=list)
    analysis_required: bool = False


class ContextUsage(BaseModel):
    used_previous_product: bool = False


class TriageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    session_id: str | None = Field(default=None, max_length=100)


class TriageOutput(BaseModel):
    trace_id: str
    triage_status: TriageStatus
    input_type: InputType
    original_query: str

    primary_intent: Intent
    secondary_intents: list[Intent] = Field(default_factory=list)

    products: list[ProductEntity] = Field(default_factory=list)
    category: str | None = None

    requested_fields: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    dietary_requirements: list[str] = Field(default_factory=list)
    nutrients: list[str] = Field(default_factory=list)

    constraints: list[Constraint] = Field(default_factory=list)
    preferences: dict[str, bool] = Field(default_factory=dict)

    comparison: Comparison = Field(default_factory=Comparison)
    subtasks: list[dict[str, Any]] = Field(default_factory=list)

    context: ContextUsage = Field(default_factory=ContextUsage)

    risk_level: RiskLevel
    unsupported_requirements: list[str] = Field(default_factory=list)
    extraction_source: str = Field(default="heuristic", description="Source or model used for extraction (e.g. gemini-2.5-flash-lite, gpt-4o-mini, barcode, heuristic)")

    clarification: Clarification = Field(default_factory=Clarification)
    routing: RoutingDecision

