import re
from uuid import uuid4

from backend.app.agents.triage.llm_extractor import extract_with_llm
from backend.app.models.triage import (
    Clarification,
    Comparison,
    Constraint,
    ContextUsage,
    InputType,
    Intent,
    ProductEntity,
    RiskLevel,
    RouteAgent,
    RoutingDecision,
    TriageOutput,
    TriageRequest,
    TriageStatus,
)
from backend.app.orchestration.routing import build_routing

BARCODE_RE = re.compile(r"^\d{8,14}$")

ALLERGEN_TERMS = {
    "peanut": ["peanut", "peanuts"],
    "milk": ["milk", "dairy", "lactose"],
    "egg": ["egg", "eggs"],
    "soy": ["soy", "soya"],
    "gluten": ["gluten", "wheat"],
    "nuts": ["tree nuts", "nuts", "hazelnut", "hazelnuts"],
}

NUTRIENT_TERMS = {
    "sugars": ["sugar", "sugars"],
    "protein": ["protein"],
    "fat": ["fat", "fats"],
    "sodium": ["sodium", "salt"],
    "energy": ["calorie", "calories", "kcal", "energy"],
}

DIETARY_TERMS = ["vegan", "vegetarian", "dairy-free", "gluten-free"]

CATEGORY_TERMS = [
    "cereal", "drink", "beverage", "biscuit", "biscuits",
    "snack", "chocolate", "yogurt", "yoghurt", "juice"
]


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def _extract_allergens(text: str) -> list[str]:
    found = []
    for canonical, terms in ALLERGEN_TERMS.items():
        if _contains_any(text, terms):
            found.append(canonical)
    return found


def _extract_nutrients(text: str) -> list[str]:
    found = []
    for canonical, terms in NUTRIENT_TERMS.items():
        if _contains_any(text, terms):
            found.append(canonical)
    return found


def _extract_dietary(text: str) -> list[str]:
    return [term for term in DIETARY_TERMS if term in text]


def _extract_category(text: str) -> str | None:
    for term in CATEGORY_TERMS:
        if term in text:
            return "beverage" if term in {"drink", "beverage", "juice"} else term.rstrip("s")
    return None


QUESTION_VERBS = {"does", "is", "can", "what", "how", "which", "tell", "show", "where", "why", "are", "do", "i", "have"}
PRONOUNS_AND_GENERIC = {"it", "this", "that", "them", "anything", "something", "product", "food", "items", "item"}


def _guess_product_names(message: str) -> list[ProductEntity]:
    """Extract candidate product names from free text."""
    products: list[ProductEntity] = []
    
    # Known common product names for quick heuristic matching
    known_products = ["nutella", "coca-cola zero", "coca-cola", "pepsi", "oreo", "kitkat", "snickers"]
    text_lower = message.lower()
    for kp in known_products:
        if kp in text_lower:
            products.append(ProductEntity(name=kp.title()))

    if not products:
        words = message.strip().split()
        first_word = words[0].lower() if words else ""
        if first_word not in QUESTION_VERBS:
            patterns = [
                r"(?:about|is|does|in|of|for|eat)\s+([A-Z][A-Za-z0-9\-\s]+?)(?:\?|,|\.| contain| have| vegan| vegetarian| high| low| and|$)",
                r"^([A-Z][A-Za-z0-9\-\s]+?)(?:\?|,|\.|$)",
            ]
            for pattern in patterns:
                match = re.search(pattern, message.strip())
                if match:
                    value = match.group(1).strip()
                    if (
                        value
                        and len(value) <= 60
                        and value.lower() not in CATEGORY_TERMS
                        and value.lower() not in PRONOUNS_AND_GENERIC
                        and value.lower().split()[0] not in QUESTION_VERBS
                    ):
                        products.append(ProductEntity(name=value))
                        break

    return products


def _heuristic_triage(message: str) -> dict:
    """Fallback heuristic extractor when LLM API is unavailable."""
    text = message.lower()
    allergens = _extract_allergens(text)
    nutrients = _extract_nutrients(text)
    dietary = _extract_dietary(text)
    category = _extract_category(text)
    products = _guess_product_names(message)

    has_allergen_q = bool(allergens) or any(
        phrase in text for phrase in ["allergic", "allergy", "contain", "contains", "does it have", "can i eat"]
    )
    has_nutrition_q = bool(nutrients) or any(
        phrase in text for phrase in ["how much sugar", "calories", "protein", "nutrition", "fat"]
    )
    has_comparison = any(
        phrase in text for phrase in ["compare", "which has", "which one", "less sugar", "more protein"]
    )
    has_recommendation = any(
        phrase in text for phrase in ["recommend", "suggest", "show me", "find me", "good options", "alternative"]
    )

    primary_intent = Intent.UNKNOWN
    secondary_intents: list[Intent] = []
    subtasks: list[dict] = []

    # Multi-intent parsing
    if has_allergen_q and has_nutrition_q:
        primary_intent = Intent.ALLERGEN_QUERY
        secondary_intents = [Intent.NUTRITION_QUERY]
        subtasks = [
            {
                "intent": "allergen_query",
                "query_fragment": "allergen safety check",
                "target_fields": ["allergens", "ingredients"],
            },
            {
                "intent": "nutrition_query",
                "query_fragment": "nutrient value check",
                "target_fields": nutrients or ["nutrition"],
            },
        ]
    elif has_allergen_q:
        primary_intent = Intent.ALLERGEN_QUERY
    elif has_dietary:
        primary_intent = Intent.DIETARY_QUERY
    elif has_comparison:
        primary_intent = Intent.COMPARISON
    elif has_recommendation:
        primary_intent = Intent.RECOMMENDATION
    elif has_nutrition_q:
        primary_intent = Intent.NUTRITION_QUERY
    elif any(term in text for term in ["ingredient", "ingredients", "tell me about", "what is"]):
        primary_intent = Intent.PRODUCT_SEARCH

    requested_fields: list[str] = []
    if "ingredient" in text:
        requested_fields.append("ingredients")
    if allergens:
        requested_fields.extend(["allergens", "ingredients"])
    requested_fields.extend(nutrients)
    if dietary:
        requested_fields.extend(["ingredients", "allergens", "dietary_suitability"])
    if primary_intent == Intent.PRODUCT_SEARCH and not requested_fields:
        requested_fields.append("general_product_info")

    return {
        "primary_intent": primary_intent,
        "secondary_intents": secondary_intents,
        "products": products,
        "category": category,
        "allergens": allergens,
        "nutrients": nutrients,
        "dietary_requirements": dietary,
        "requested_fields": list(dict.fromkeys(requested_fields)),
        "constraints": [],
        "subtasks": subtasks,
        "unsupported_requirements": [],
    }


def triage_message(request: TriageRequest) -> TriageOutput:
    message = request.message.strip()
    text = message.lower()
    barcode_only = bool(BARCODE_RE.fullmatch(message))

    # 1. Handle exact barcode lookup deterministically
    if barcode_only:
        product = ProductEntity(barcode=message)
        routing = build_routing(Intent.BARCODE_LOOKUP)
        return TriageOutput(
            trace_id=f"REQ-{uuid4().hex[:8].upper()}",
            triage_status=TriageStatus.READY,
            input_type=InputType.BARCODE,
            original_query=message,
            primary_intent=Intent.BARCODE_LOOKUP,
            secondary_intents=[],
            products=[product],
            category=None,
            requested_fields=["general_product_info", "ingredients", "nutrition"],
            allergens=[],
            dietary_requirements=[],
            nutrients=[],
            constraints=[],
            preferences={},
            comparison=Comparison(),
            subtasks=[],
            context=ContextUsage(),
            risk_level=RiskLevel.LOW,
            unsupported_requirements=[],
            clarification=Clarification(),
            routing=routing,
        )

    # 2. Attempt LLM Structured Extraction
    llm_extracted = extract_with_llm(message)
    if llm_extracted:
        primary_intent = llm_extracted.primary_intent
        secondary_intents = llm_extracted.secondary_intents
        products = llm_extracted.products
        category = llm_extracted.category
        allergens = llm_extracted.allergens
        nutrients = llm_extracted.nutrients
        dietary_requirements = llm_extracted.dietary_requirements
        requested_fields = llm_extracted.requested_fields
        constraints = llm_extracted.constraints
        subtasks = llm_extracted.subtasks
        unsupported_requirements = llm_extracted.unsupported_requirements
    else:
        # Fallback to upgraded heuristic extraction
        parsed = _heuristic_triage(message)
        primary_intent = parsed["primary_intent"]
        secondary_intents = parsed["secondary_intents"]
        products = parsed["products"]
        category = parsed["category"]
        allergens = parsed["allergens"]
        nutrients = parsed["nutrients"]
        dietary_requirements = parsed["dietary_requirements"]
        requested_fields = parsed["requested_fields"]
        constraints = parsed["constraints"]
        subtasks = parsed["subtasks"]
        unsupported_requirements = parsed["unsupported_requirements"]

    # 3. Deterministic Python Safety & Risk Assessment
    if allergens or primary_intent == Intent.ALLERGEN_QUERY or Intent.ALLERGEN_QUERY in secondary_intents:
        risk_level = RiskLevel.HIGH
    elif primary_intent in {
        Intent.NUTRITION_QUERY,
        Intent.COMPARISON,
        Intent.DIETARY_QUERY,
        Intent.RECOMMENDATION,
    } or any(i in {Intent.NUTRITION_QUERY, Intent.COMPARISON, Intent.DIETARY_QUERY} for i in secondary_intents):
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW

    # 4. Check Clarification Need
    needs_product = primary_intent in {
        Intent.PRODUCT_SEARCH,
        Intent.ALLERGEN_QUERY,
        Intent.NUTRITION_QUERY,
        Intent.DIETARY_QUERY,
    }
    has_valid_product = any(p.name or p.barcode for p in products)

    missing_fields: list[str] = []
    if needs_product and not has_valid_product:
        missing_fields.append("product")

    if missing_fields:
        status = TriageStatus.CLARIFICATION_REQUIRED
        clarification = Clarification(
            required=True,
            missing_fields=missing_fields,
            question="Which product would you like me to check?",
        )
        routing = RoutingDecision(
            next_agent=None,
            required_agents=[],
            analysis_required=False,
        )
    elif primary_intent == Intent.UNKNOWN:
        status = TriageStatus.UNSUPPORTED
        clarification = Clarification()
        routing = RoutingDecision(
            next_agent=RouteAgent.RESPONSE,
            required_agents=[RouteAgent.RESPONSE],
            analysis_required=False,
        )
    else:
        status = TriageStatus.READY
        clarification = Clarification()
        routing = build_routing(primary_intent)
        # Ensure Analysis agent is included for secondary allergen/nutrition intents
        if (
            Intent.ALLERGEN_QUERY in secondary_intents
            or Intent.NUTRITION_QUERY in secondary_intents
            or Intent.DIETARY_QUERY in secondary_intents
        ):
            if RouteAgent.ANALYSIS not in routing.required_agents:
                routing.required_agents.insert(1, RouteAgent.ANALYSIS)
                routing.analysis_required = True

    return TriageOutput(
        trace_id=f"REQ-{uuid4().hex[:8].upper()}",
        triage_status=status,
        input_type=InputType.NATURAL_LANGUAGE,
        original_query=message,
        primary_intent=primary_intent,
        secondary_intents=secondary_intents,
        products=products,
        category=category,
        requested_fields=requested_fields,
        allergens=allergens,
        dietary_requirements=dietary_requirements,
        nutrients=nutrients,
        constraints=constraints,
        preferences={},
        comparison=Comparison(),
        subtasks=subtasks,
        context=ContextUsage(),
        risk_level=risk_level,
        unsupported_requirements=unsupported_requirements,
        clarification=clarification,
        routing=routing,
    )
