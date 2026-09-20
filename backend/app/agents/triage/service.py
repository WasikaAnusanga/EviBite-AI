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

from backend.app.security.guard import sanitize_user_query

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
    "sugar": ["sugar", "sugars"],
    "protein": ["protein", "proteins"],
    "fat": ["fat", "fats"],
    "sodium": ["sodium", "salt"],
    "calories": ["calorie", "calories", "kcal", "energy"],
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
            if canonical == "sugar" and "sugars" not in found:
                found.append("sugars")
    return found


def _extract_dietary(text: str) -> list[str]:
    return [term for term in DIETARY_TERMS if term in text]


def _extract_category(text: str) -> str | None:
    for term in CATEGORY_TERMS:
        if term in text:
            return "beverage" if term in {"drink", "beverage", "juice"} else term.rstrip("s")
    return None


CANONICAL_NUTRIENTS = {
    "sugar": ["sugar", "sugars"],
    "protein": ["protein", "proteins"],
    "fat": ["fat", "fats"],
    "saturated_fat": ["saturated fat", "sat fat", "saturated_fat"],
    "calories": ["calorie", "calories", "kcal", "energy"],
    "sodium": ["sodium", "salt"],
    "carbohydrates": ["carbs", "carbohydrate", "carbohydrates"],
    "fibre": ["fibre", "fiber"],
}


def _canonicalize_nutrient(name: str) -> str:
    name_lower = name.lower().strip()
    for canonical, synonyms in CANONICAL_NUTRIENTS.items():
        if name_lower in synonyms or any(syn in name_lower for syn in synonyms):
            return canonical
    return name_lower


def _extract_constraints(text: str) -> list[Constraint]:
    constraints: list[Constraint] = []
    text_lower = text.lower()

    pattern_nutrient_first = r"(sugar|sugars|fat|fats|protein|sodium|salt|calories|calorie|energy|carbs|carbohydrates|fibre|fiber|saturated fat)\s*(less\s+than|under|below|<=|<|more\s+than|over|above|>=|>|at\s+most|at\s+least|equal\s+to|=)\s*(\d+(?:\.\d+)?)\s*(g|mg|kcal|cal)?"
    pattern_op_first = r"(less\s+than|under|below|<=|<|more\s+than|over|above|>=|>|at\s+most|at\s+least|equal\s+to|=)\s*(\d+(?:\.\d+)?)\s*(g|mg|kcal|cal)?\s*(sugar|sugars|fat|fats|protein|sodium|salt|calories|calorie|energy|carbs|carbohydrates|fibre|fiber|saturated fat)?"

    processed_nutrients = set()

    for m in re.finditer(pattern_nutrient_first, text_lower):
        nut_str, op_str, val_str, unit = m.groups()
        val = float(val_str)
        nut = _canonicalize_nutrient(nut_str)
        if op_str in ["less than", "under", "below", "<"]:
            op = "lt"
            pref = "minimize"
        elif op_str in ["<=", "at most"]:
            op = "lte"
            pref = "minimize"
        elif op_str in ["more than", "over", "above", ">"]:
            op = "gt"
            pref = "maximize"
        elif op_str in [">=", "at least"]:
            op = "gte"
            pref = "maximize"
        elif op_str in ["=", "equal to"]:
            op = "eq"
            pref = "none"
        else:
            op = "lte"
            pref = "minimize"

        c = Constraint(nutrient=nut, operator=op, value=val, unit=unit or "g", preference=pref)
        constraints.append(c)
        processed_nutrients.add(nut)

    for m in re.finditer(pattern_op_first, text_lower):
        op_str, val_str, unit, nut_str = m.groups()
        val = float(val_str)
        nut = _canonicalize_nutrient(nut_str) if nut_str else "sugar"
        if nut in processed_nutrients:
            continue
        if op_str in ["less than", "under", "below", "<"]:
            op = "lt"
            pref = "minimize"
        elif op_str in ["<=", "at most"]:
            op = "lte"
            pref = "minimize"
        elif op_str in ["more than", "over", "above", ">"]:
            op = "gt"
            pref = "maximize"
        elif op_str in [">=", "at least"]:
            op = "gte"
            pref = "maximize"
        elif op_str in ["=", "equal to"]:
            op = "eq"
            pref = "none"
        else:
            op = "lte"
            pref = "minimize"

        c = Constraint(nutrient=nut, operator=op, value=val, unit=unit or "g", preference=pref)
        constraints.append(c)
        processed_nutrients.add(nut)

    qualitative_high = ["high", "rich in", "more", "higher", "increased", "lots of", "plenty of"]
    qualitative_low = ["low", "less", "lower", "reduced", "minimal", "without high"]

    for canonical, synonyms in CANONICAL_NUTRIENTS.items():
        if canonical in processed_nutrients:
            continue
        found_syn = next((s for s in synonyms if s in text_lower), None)
        if found_syn:
            if any(f"{h} {found_syn}" in text_lower or f"{found_syn} {h}" in text_lower for h in qualitative_high):
                c = Constraint(nutrient=canonical, operator=None, value=None, unit=None, preference="maximize")
                constraints.append(c)
                processed_nutrients.add(canonical)
            elif any(f"{l} {found_syn}" in text_lower or f"{found_syn} {l}" in text_lower for l in qualitative_low):
                c = Constraint(nutrient=canonical, operator=None, value=None, unit=None, preference="minimize")
                constraints.append(c)
                processed_nutrients.add(canonical)
            elif any(h in text_lower for h in qualitative_high) and canonical in ["protein", "fibre", "carbohydrates"]:
                c = Constraint(nutrient=canonical, operator=None, value=None, unit=None, preference="maximize")
                constraints.append(c)
                processed_nutrients.add(canonical)
            elif any(l in text_lower for l in qualitative_low) and canonical in ["sugar", "fat", "saturated_fat", "sodium", "calories"]:
                c = Constraint(nutrient=canonical, operator=None, value=None, unit=None, preference="minimize")
                constraints.append(c)
                processed_nutrients.add(canonical)

    return constraints



def _extract_comparison(text: str) -> Comparison:
    metric = None
    goal = None
    if "sugar" in text or "sugars" in text:
        metric = "sugars"
    elif "protein" in text:
        metric = "protein"
    elif "fat" in text or "fats" in text:
        metric = "fat"
    elif "calorie" in text or "calories" in text:
        metric = "energy"

    if any(w in text for w in ["less", "lower", "fewer", "least", "lowest", "reduce"]):
        goal = "lower"
    elif any(w in text for w in ["more", "higher", "highest", "most"]):
        goal = "higher"
    elif "equal" in text or "same" in text:
        goal = "equal"

    return Comparison(metric=metric, goal=goal)


QUESTION_VERBS = {"does", "is", "can", "what", "how", "which", "tell", "show", "where", "why", "are", "do", "i", "have"}
PRONOUNS_AND_GENERIC = {"it", "this", "that", "them", "anything", "something", "product", "food", "items", "item"}


def _guess_product_names(message: str) -> list[ProductEntity]:
    """Extract candidate product names from free text."""
    products: list[ProductEntity] = []
    seen_names = set()
    
    known_products = [
        "coca-cola zero", "coke zero", "coca-cola", "coke", "pepsi", "nutella",
        "oreo", "cheerios", "special k", "kitkat", "snickers"
    ]
    text_lower = message.lower()
    for kp in known_products:
        if kp in text_lower and kp not in seen_names:
            seen_names.add(kp)
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
    constraints = _extract_constraints(text)
    comparison = _extract_comparison(text)

    has_dietary = bool(dietary) or any(phrase in text for phrase in ["vegan", "vegetarian", "dairy-free", "gluten-free"])
    has_allergen_q = bool(allergens) or any(
        phrase in text for phrase in ["allergic", "allergy", "hazelnut", "hazelnuts", "peanut", "peanuts", "milk", "gluten"]
    )
    if not has_allergen_q and not has_dietary and any(phrase in text for phrase in ["contain", "contains", "does it have", "can i eat"]):
        has_allergen_q = True

    has_nutrition_q = bool(nutrients) or any(
        phrase in text for phrase in ["how much sugar", "calories", "protein", "nutrition", "fat"]
    )
    has_comparison = any(
        phrase in text for phrase in ["compare", "which has", "which one", "versus", " vs ", "less sugar", "more protein"]
    )
    has_recommendation = any(
        phrase in text for phrase in ["recommend", "suggest", "show me", "find me", "good options", "alternative", "i want"]
    )

    greeting_terms = ["hi", "hello", "hey", "good morning", "good afternoon", "greetings", "thanks", "thank you", "who are you", "what can you do", "help", "who made you"]
    clean_text = re.sub(r"[^\w\s]", "", text)
    is_greeting = any(
        clean_text == term or clean_text.startswith(term + " ") or clean_text.endswith(" " + term) or f" {term} " in clean_text
        for term in greeting_terms
    ) and not (has_allergen_q or has_nutrition_q or has_comparison or has_recommendation or has_dietary or products)

    primary_intent = Intent.UNKNOWN
    secondary_intents: list[Intent] = []
    subtasks: list[dict] = []

    # Multi-intent parsing
    if is_greeting:
        primary_intent = Intent.GREETING
    elif has_comparison:
        primary_intent = Intent.PRODUCT_COMPARISON if len(products) >= 2 else Intent.NUTRIENT_COMPARISON
    elif has_dietary:
        primary_intent = Intent.DIETARY_COMPLIANCE
    elif has_recommendation or (category and (constraints or "high" in text or "low" in text or "under" in text or "over" in text)):
        primary_intent = Intent.RECOMMENDATION
    elif has_allergen_q and has_nutrition_q:
        primary_intent = Intent.ALLERGEN_CHECK
        secondary_intents = [Intent.NUTRITION_QUERY]
        subtasks = [
            {
                "intent": "allergen_check",
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
        primary_intent = Intent.ALLERGEN_CHECK
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
        "constraints": constraints,
        "comparison": comparison,
        "subtasks": subtasks,
        "unsupported_requirements": [],
    }



def triage_message(request: TriageRequest) -> TriageOutput:
    message = request.message.strip()
    text = message.lower()

    # 0. Prompt Injection & Security Guard Interceptor
    is_safe, sanitized_or_reason = sanitize_user_query(message)
    if not is_safe:
        return TriageOutput(
            trace_id=f"REQ-{uuid4().hex[:8].upper()}",
            triage_status=TriageStatus.UNSUPPORTED,
            input_type=InputType.NATURAL_LANGUAGE,
            original_query=message,
            primary_intent=Intent.UNKNOWN,
            secondary_intents=[],
            products=[],
            category=None,
            requested_fields=[],
            allergens=[],
            dietary_requirements=[],
            nutrients=[],
            constraints=[],
            preferences={},
            comparison=Comparison(),
            subtasks=[],
            context=ContextUsage(),
            risk_level=RiskLevel.LOW,
            unsupported_requirements=["prompt_injection_attempt"],
            clarification=Clarification(),
            routing=RoutingDecision(
                next_agent=RouteAgent.RESPONSE,
                required_agents=[RouteAgent.RESPONSE],
                analysis_required=False,
            ),
        )

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
        comparison = Comparison()
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
        comparison = parsed.get("comparison", Comparison())
        subtasks = parsed["subtasks"]
        unsupported_requirements = parsed["unsupported_requirements"]


    # Detect store inventory / non-food out-of-domain terms
    store_terms = ["price", "cost", "stock", "aisle", "shelf", "branch", "location", "discount", "where to buy"]
    for st in store_terms:
        if st in text and st not in unsupported_requirements:
            unsupported_requirements.append(st)

    # 3. Context & Pronoun Resolution ("it", "this", "that")
    used_previous_product = False
    has_valid_product = any(p.name or p.barcode for p in products)
    pronouns = {"it", "this", "that", "them"}
    has_pronoun = bool(set(text.split()).intersection(pronouns)) or "does it" in text or "is it" in text

    if request.previous_product and (not has_valid_product or has_pronoun):
        if request.previous_product.name or request.previous_product.barcode:
            products = [request.previous_product]
            has_valid_product = True
            used_previous_product = True

    # 4. Deterministic Python Safety & Risk Assessment
    if allergens or primary_intent in {Intent.ALLERGEN_CHECK, Intent.ALLERGEN_QUERY} or Intent.ALLERGEN_CHECK in secondary_intents:
        risk_level = RiskLevel.HIGH
    elif primary_intent in {
        Intent.NUTRITION_QUERY,
        Intent.PRODUCT_COMPARISON,
        Intent.NUTRIENT_COMPARISON,
        Intent.COMPARISON,
        Intent.DIETARY_COMPLIANCE,
        Intent.DIETARY_QUERY,
        Intent.RECOMMENDATION,
    } or any(i in {Intent.NUTRITION_QUERY, Intent.PRODUCT_COMPARISON, Intent.NUTRIENT_COMPARISON, Intent.DIETARY_COMPLIANCE} for i in secondary_intents):
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW

    # 5. Check Clarification Need & Out-of-Domain Status
    needs_product = primary_intent in {
        Intent.PRODUCT_SEARCH,
        Intent.ALLERGEN_CHECK,
        Intent.ALLERGEN_QUERY,
        Intent.NUTRITION_QUERY,
        Intent.DIETARY_COMPLIANCE,
        Intent.DIETARY_QUERY,
    }

    missing_fields: list[str] = []
    if needs_product and not has_valid_product:
        missing_fields.append("product")

    # If pure store query with no food query elements, treat as unsupported/out_of_domain
    is_pure_store_query = bool(unsupported_requirements) and not (
        allergens or nutrients or dietary_requirements or has_valid_product or primary_intent in {
            Intent.ALLERGEN_CHECK, Intent.ALLERGEN_QUERY, Intent.NUTRITION_QUERY, Intent.DIETARY_COMPLIANCE, Intent.DIETARY_QUERY, Intent.PRODUCT_SEARCH
        }
    )

    if is_pure_store_query or primary_intent in {Intent.UNKNOWN, Intent.OUT_OF_DOMAIN}:
        status = TriageStatus.UNSUPPORTED
        clarification = Clarification()
        routing = RoutingDecision(
            next_agent=RouteAgent.RESPONSE,
            required_agents=[RouteAgent.RESPONSE],
            analysis_required=False,
        )
    elif missing_fields:
        status = TriageStatus.CLARIFICATION_REQUIRED
        q_target = f"for {allergens[0]}" if allergens else ""
        clarification = Clarification(
            required=True,
            missing_fields=missing_fields,
            question=f"Which product would you like me to check{(' ' + q_target) if q_target else ''}?",
        )
        routing = RoutingDecision(
            next_agent=None,
            required_agents=[],
            analysis_required=False,
        )
    else:
        status = TriageStatus.READY if not unsupported_requirements else TriageStatus.PARTIALLY_SUPPORTED
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
        nutrient_constraints=constraints,
        constraints=constraints,
        preferences={},
        comparison=comparison,
        subtasks=subtasks,

        context=ContextUsage(used_previous_product=used_previous_product),
        risk_level=risk_level,
        unsupported_requirements=unsupported_requirements,
        clarification=clarification,
        routing=routing,
    )

