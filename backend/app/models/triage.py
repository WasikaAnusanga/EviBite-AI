from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Intent(str, Enum):
    PRODUCT_SEARCH = "product_search"
    BARCODE_LOOKUP = "barcode_lookup"
    ALLERGEN_CHECK = "allergen_check"
    ALLERGEN_QUERY = "allergen_check"
    DIETARY_COMPLIANCE = "dietary_compliance"
    DIETARY_QUERY = "dietary_compliance"
    NUTRITION_QUERY = "nutrition_query"
    NUTRIENT_COMPARISON = "nutrient_comparison"
    PRODUCT_COMPARISON = "product_comparison"
    COMPARISON = "product_comparison"
    RECOMMENDATION = "recommendation"
    GREETING = "greeting"
    OUT_OF_DOMAIN = "out_of_domain"
    UNSUPPORTED = "out_of_domain"
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


class NutrientConstraint(BaseModel):
    nutrient: str
    operator: Literal["lt", "lte", "gt", "gte", "eq"] | None = None
    value: float | None = None
    unit: str | None = None
    preference: Literal["minimize", "maximize", "none"] = "none"

    @property
    def field(self) -> str:
        return self.nutrient


# Alias for backward compatibility
Constraint = NutrientConstraint


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
    previous_product: ProductEntity | None = Field(default=None)


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

    nutrient_constraints: list[NutrientConstraint] = Field(default_factory=list)
    constraints: list[NutrientConstraint] = Field(default_factory=list)
    preferences: dict[str, bool] = Field(default_factory=dict)

    comparison: Comparison = Field(default_factory=Comparison)
    subtasks: list[dict[str, Any]] = Field(default_factory=list)

    context: ContextUsage = Field(default_factory=ContextUsage)

    risk_level: RiskLevel
    unsupported_requirements: list[str] = Field(default_factory=list)

    clarification: Clarification = Field(default_factory=Clarification)
    routing: RoutingDecision

    @property
    def intent(self) -> str:
        return self.primary_intent.value

    @property
    def product_names(self) -> list[str]:
        return [p.name for p in self.products if p.name]

    @property
    def brand(self) -> str | None:
        for p in self.products:
            if p.brand:
                return p.brand
        return None

    @property
    def barcode(self) -> str | None:
        for p in self.products:
            if p.barcode:
                return p.barcode
        return None

    @property
    def comparison_targets(self) -> list[str]:
        return [self.comparison.metric] if self.comparison and self.comparison.metric else []

    @property
    def needs_clarification(self) -> bool:
        return self.clarification.required

    @property
    def clarification_question(self) -> str | None:
        return self.clarification.question

    @property
    def route(self) -> str | None:
        return self.routing.next_agent.value if self.routing.next_agent else None

