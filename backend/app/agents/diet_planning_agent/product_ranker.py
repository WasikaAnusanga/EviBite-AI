"""Supermarket Product Retrieval & Multi-Factor Ranking Engine.

Retrieves genuine supermarket items and scores them using the multi-factor formula:
Final Score = Nutrition Score + Goal Match Score + Preference Score + Budget Score - Allergen Penalty
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.app.agents.agent_stubs import EvidenceObject, RetrievalRequest
from backend.app.agents.diet_planning_agent.schemas import (
    BudgetLevel,
    CookingPreference,
    DietPreference,
    DietProfile,
    HealthGoal,
    NutritionTargets,
    RankedProductItem,
)
from backend.app.agents.retrieval.service import retrieval_service
from backend.app.db.product_repository import product_repo

logger = logging.getLogger(__name__)


# Curated functional food pillars per meal slot
MEAL_SLOT_PILLARS: Dict[str, List[List[str]]] = {
    "breakfast": [
        ["whole wheat bread", "sourdough bread", "rolled oats", "weetabix 100%", "rye bread"],
        ["eggs", "almond milk", "chobani greek yogurt", "tofu", "oat milk"],
        ["peanut butter", "chia seeds", "apple", "banana", "mixed berries", "strawberries"],
    ],
    "lunch": [
        ["chicken breast", "canned tuna in water", "salmon fillets", "lentils", "tofu", "canned black beans"],
        ["brown rice", "quinoa", "sweet potato", "whole grain wrap"],
        ["mixed salad greens", "spinach", "broccoli florets", "cucumber", "baby carrots"],
    ],
    "dinner": [
        ["salmon fillets", "turkey breast", "chicken breast", "chickpeas", "cod fillets", "tofu"],
        ["sweet potato", "quinoa", "brown rice", "lentils", "black beans"],
        ["steamed vegetables", "spinach", "broccoli", "green beans", "mixed vegetables"],
    ],
    "snack": [
        ["raw almonds", "walnuts", "peanut butter", "pumpkin seeds"],
        ["rice cakes", "dark chocolate 70%", "protein bar"],
        ["green apple", "banana", "fresh blueberries"],
    ],
}


def classify_food_group(product: EvidenceObject) -> str:
    """Classifies a product into a functional nutritional food group."""
    name = product.name.lower()

    # Check title first to avoid Open Food Facts broad category over-generalization
    if any(k in name for k in ["chips", "crisps", "tortilla chips", "pringles", "snack"]):
        return "junk_snacks"
    if any(k in name for k in ["dark chocolate", "rice cake", "rice cakes", "protein bar", "killa"]):
        return "healthy_snacks"
    if any(k in name for k in ["tuna", "salmon", "saumon", "thon", "poisson", "pescado", "cod", "sardine", "mackerel", "prawn", "shrimp", "fish", "seafood"]):
        return "fish_seafood"
    if any(k in name for k in ["chicken", "poulet", "pollo", "turkey", "dinde", "pavo", "beef", "steak", "pork", "ham"]):
        return "poultry_meat"
    if any(k in name for k in ["egg", "eggs", "oeuf", "oeufs", "huevo"]):
        return "eggs"
    if any(k in name for k in ["bread", "toast", "bagel", "wrap", "tortilla", "pitta", "sourdough", "crumpet", "wholemeal", "pain"]):
        return "bakery_grains"
    if any(k in name for k in ["oat", "porridge", "oatmeal", "cheerios", "weetabix", "muesli", "granola", "corn flakes", "avena", "avoine", "crisp"]):
        return "cereal_oats"
    if any(k in name for k in ["tofu", "tempeh", "lentil", "lentils", "lentilles", "lentejas", "chickpea", "chickpeas", "pois chiches", "garbanzo", "black beans", "kidney beans", "beans", "haricots", "edamame"]):
        return "plant_protein"
    if any(k in name for k in ["yogurt", "yoghurt", "cheese", "cottage cheese", "fromage", "queso"]):
        return "dairy_protein"
    if any(k in name for k in ["almond milk", "oat milk", "soya milk", "soy milk", "coconut milk"]):
        return "plant_milk"
    if any(k in name for k in ["almond", "walnut", "cashew", "nuts", "nut", "seeds", "chia", "flax", "sesame", "sésame", "noix", "peanut butter", "almond butter"]):
        return "nuts_seeds"
    if any(k in name for k in ["apple", "banana", "berry", "berries", "orange", "grape", "fruit", "smoothie", "pomme", "fraise"]):
        return "fruits"
    if any(k in name for k in ["spinach", "broccoli", "carrot", "salad", "greens", "kale", "vegetable", "tomato", "cucumber", "potato", "sweet potato", "epinards", "salade"]):
        return "vegetables"
    if any(k in name for k in ["rice", "quinoa", "pasta", "noodle", "couscous", "arroz", "riz"]):
        return "starchy_carbs"

    return "general"


def _is_condiment_or_non_meal(product: EvidenceObject) -> bool:
    """Filter out stock cubes, seasonings, bouillon, gravy powders, flavour sachets, and baking additives."""
    text = f"{product.name} {product.ingredients_text or ''} {' '.join(product.categories)}".lower()
    excluded_keywords = [
        "stock cube", "stock cubes", "bouillon", "seasoning", "flavour", "flavor",
        "sachet", "powder", "yeast", "extract", "gravy", "broth cubes", "additive",
        "sweetener", "baking powder", "gelatin", "gelatine", "sauce packet",
        "stock pot", "marinade", "stock concentrate", "flavouring", "flavoring",
        "seasoning mix", "stock powder"
    ]
    if any(k in text for k in excluded_keywords):
        return True

    # Exclude products with excessive sodium (almost always seasoning cubes/salts)
    sod = float(product.nutrition.get("sodium_mg_100g") or 0.0)
    if sod > 2000.0:
        return True

    # Exclude negligible-calorie items (unless unsweetened tea or water)
    cal = float(product.nutrition.get("energy_kcal_100g") or 0.0)
    if cal < 15.0 and not any(w in text for w in ["water", "tea", "coffee"]):
        return True

    return False


def _matches_any_keyword(text: str, keywords: List[str]) -> bool:
    """Check if any keyword appears in the target string."""
    if not text or not keywords:
        return False
    lower_text = text.lower()
    for kw in keywords:
        kw_clean = kw.strip().lower()
        if kw_clean and (kw_clean in lower_text or re.search(rf"\b{re.escape(kw_clean)}\b", lower_text)):
            return True
    return False


def _check_allergen_conflict(product: EvidenceObject, allergies: List[str]) -> bool:
    """Check if the product contains any user-declared allergens."""
    if not allergies:
        return False

    prod_allergens = [a.lower() for a in product.allergens]
    ingredients = (product.ingredients_text or "").lower()
    prod_name = product.name.lower()

    allergen_synonyms = {
        "milk": ["milk", "dairy", "whey", "casein", "lactose", "butter", "cheese", "cream", "yogurt"],
        "eggs": ["egg", "eggs", "albumin", "egg yolk", "egg white"],
        "peanuts": ["peanut", "peanuts", "groundnut", "arachis"],
        "tree nuts": ["tree nuts", "almond", "almonds", "walnut", "hazelnut", "cashew", "pistachio", "pecan"],
        "gluten": ["gluten", "wheat", "barley", "rye", "spelt"],
        "seafood": ["fish", "salmon", "tuna", "shrimp", "prawn", "crab", "lobster", "crustacean", "mollusc"],
        "soy": ["soy", "soya", "soybean", "tofu", "edamame"],
    }

    for user_allergy in allergies:
        clean_user_alg = user_allergy.strip().lower()
        synonyms = allergen_synonyms.get(clean_user_alg, [clean_user_alg])

        # Check declared allergens list
        for syn in synonyms:
            if any(syn in pa for pa in prod_allergens):
                return True
            # Check ingredients text
            if ingredients and re.search(rf"\b{re.escape(syn)}\b", ingredients):
                return True
            # Check product title
            if re.search(rf"\b{re.escape(syn)}\b", prod_name):
                return True

    return False


def _check_dietary_compatibility(product: EvidenceObject, diet: DietPreference) -> Tuple[bool, float]:
    """Check compatibility with dietary lifestyle (Vegan, Vegetarian, Keto, etc.)."""
    non_veg_keywords = ["chicken", "beef", "pork", "meat", "fish", "salmon", "tuna", "turkey", "gelatin", "ham", "bacon"]
    dairy_egg_keywords = ["milk", "cheese", "yogurt", "butter", "whey", "casein", "egg", "eggs", "honey"]

    name_and_ingr = f"{product.name} {product.ingredients_text or ''} {' '.join(product.categories)}".lower()

    if diet == DietPreference.VEGAN:
        if _matches_any_keyword(name_and_ingr, non_veg_keywords + dairy_egg_keywords):
            return False, -2.0
        return True, 0.4

    if diet == DietPreference.VEGETARIAN:
        if _matches_any_keyword(name_and_ingr, non_veg_keywords):
            return False, -2.0
        return True, 0.4

    if diet == DietPreference.KETO:
        sugars = product.nutrition.get("sugars_g_100g") or 0.0
        carbs = product.nutrition.get("carbohydrates_100g")
        if carbs is None:
            # Estimate carbs from energy and protein/fat if not present
            kcal = product.nutrition.get("energy_kcal_100g") or 0.0
            prot = product.nutrition.get("protein_g_100g") or 0.0
            fat = product.nutrition.get("fat_g_100g") or 0.0
            carbs = max(0.0, (kcal - (prot * 4 + fat * 9)) / 4.0)

        if carbs > 10.0 or sugars > 6.0:
            return False, -1.0
        return True, 0.5

    if diet == DietPreference.HIGH_PROTEIN:
        prot = product.nutrition.get("protein_g_100g") or 0.0
        if prot >= 10.0:
            return True, 0.5
        return True, 0.1

    if diet == DietPreference.LOW_CARB:
        sugars = product.nutrition.get("sugars_g_100g") or 0.0
        if sugars > 10.0:
            return False, -0.6
        return True, 0.3

    return True, 0.2


def score_product(
    product: EvidenceObject,
    profile: DietProfile,
    targets: NutritionTargets,
    meal_slot: str = "general",
) -> Tuple[float, Dict[str, float]]:
    """Calculates multi-factor score for a supermarket product."""
    nutrition = product.nutrition
    protein_g = float(nutrition.get("protein_g_100g") or 0.0)
    energy_kcal = float(nutrition.get("energy_kcal_100g") or 0.0)
    sugars_g = float(nutrition.get("sugars_g_100g") or 0.0)
    fat_g = float(nutrition.get("fat_g_100g") or 0.0)
    sat_fat_g = float(nutrition.get("saturated_fat_g_100g") or 0.0)
    fiber_g = float(nutrition.get("fiber_g_100g") or 0.0)
    sodium_mg = float(nutrition.get("sodium_mg_100g") or 0.0)

    # 1. ALLERGEN PENALTY (CRITICAL)
    has_allergen = _check_allergen_conflict(product, profile.allergies)
    allergen_penalty = 10.0 if has_allergen else 0.0

    # Foods to avoid penalty
    avoid_words = [w.strip().lower() for w in profile.foods_to_avoid.split(",") if w.strip()]
    if _matches_any_keyword(f"{product.name} {product.ingredients_text or ''}", avoid_words):
        allergen_penalty += 8.0

    # 2. NUTRITION SCORE (0.0 to 1.0)
    nutr_score = 0.5  # neutral baseline

    # Protein contribution
    nutr_score += min(0.35, (protein_g / 25.0) * 0.35)

    # Sugar moderation
    if sugars_g <= 4.0:
        nutr_score += 0.2
    elif sugars_g > 15.0:
        nutr_score -= min(0.35, ((sugars_g - 15.0) / 30.0) * 0.35)

    # Fiber bonus
    if fiber_g >= 3.0:
        nutr_score += 0.15

    # Saturated fat moderation
    if sat_fat_g > 10.0:
        nutr_score -= min(0.2, (sat_fat_g / 25.0) * 0.2)

    # Sodium penalty if excessively high
    if sodium_mg > 700.0:
        nutr_score -= 0.15

    # Health Condition penalties
    conds = [c.lower() for c in profile.health_conditions]
    if "diabetes" in conds and sugars_g > 6.0:
        nutr_score -= 0.35
    if ("high_blood_pressure" in conds or "hypertension" in conds) and sodium_mg > 400.0:
        nutr_score -= 0.35
    if "high_cholesterol" in conds and sat_fat_g > 4.0:
        nutr_score -= 0.3

    nutr_score = max(0.0, min(1.0, nutr_score))

    # 3. GOAL MATCH SCORE (0.0 to 1.0)
    goal_score = 0.5
    if profile.goal == HealthGoal.MUSCLE_GAIN:
        # High protein reward & supportive calories
        if protein_g >= 12.0:
            goal_score = 0.95
        elif protein_g >= 7.0:
            goal_score = 0.75
        elif energy_kcal >= 250 and sugars_g < 10.0:
            goal_score = 0.70  # healthy caloric fuel
        else:
            goal_score = 0.40

    elif profile.goal == HealthGoal.WEIGHT_LOSS:
        # High protein + low calorie density + low sugar
        if protein_g >= 10.0 and energy_kcal <= 200.0:
            goal_score = 0.95
        elif sugars_g <= 3.0 and energy_kcal <= 150.0:
            goal_score = 0.85
        elif energy_kcal > 350.0 and protein_g < 10.0:
            goal_score = 0.20  # penalize empty high-calorie foods
        else:
            goal_score = 0.50

    elif profile.goal == HealthGoal.WEIGHT_GAIN:
        if energy_kcal >= 300.0 and sugars_g < 15.0:
            goal_score = 0.90
        elif protein_g >= 10.0:
            goal_score = 0.80
        else:
            goal_score = 0.50

    elif profile.goal in (HealthGoal.MAINTAIN_WEIGHT, HealthGoal.GENERAL_HEALTH):
        if sugars_g <= 8.0 and sat_fat_g <= 5.0 and protein_g >= 5.0:
            goal_score = 0.90
        else:
            goal_score = 0.60

    goal_score = max(0.0, min(1.0, goal_score))

    # 4. PREFERENCE SCORE (0.0 to 1.0)
    pref_score = 0.4

    # Lifestyle compatibility
    compatible, diet_adj = _check_dietary_compatibility(product, profile.diet)
    pref_score += diet_adj

    # User favorite foods matching
    fav_words = [w.strip().lower() for w in profile.food_preferences.split(",") if w.strip()]
    if _matches_any_keyword(f"{product.name} {product.brand or ''}", fav_words):
        pref_score += 0.35

    # Cooking preference matching
    if profile.cooking_preference == CookingPreference.NO_COOKING:
        ready_to_eat_kw = ["bar", "yogurt", "milk", "cereal", "bread", "fruit", "nuts", "seeds", "snack", "cheese"]
        if _matches_any_keyword(product.name, ready_to_eat_kw):
            pref_score += 0.2

    pref_score = max(0.0, min(1.0, pref_score))

    # 5. BUDGET SCORE (0.0 to 0.5)
    budget_score = 0.3
    staple_keywords = ["oats", "rice", "beans", "eggs", "milk", "lentils", "tuna", "bread", "banana", "yogurt"]
    is_staple = _matches_any_keyword(product.name, staple_keywords)

    if profile.budget == BudgetLevel.LOW:
        budget_score = 0.5 if is_staple else 0.2
    elif profile.budget == BudgetLevel.HIGH:
        budget_score = 0.45  # Flexible budget for premium products
    else:
        budget_score = 0.4 if is_staple else 0.3

    # FINAL FORMULA
    final_score = round(
        nutr_score + goal_score + pref_score + budget_score - allergen_penalty, 3
    )

    breakdown = {
        "nutrition_score": round(nutr_score, 3),
        "goal_match_score": round(goal_score, 3),
        "preference_score": round(pref_score, 3),
        "budget_score": round(budget_score, 3),
        "allergen_penalty": round(allergen_penalty, 3),
        "final_score": final_score,
    }

    return final_score, breakdown


def retrieve_and_rank_products_for_slot(
    slot_name: str,
    profile: DietProfile,
    targets: NutritionTargets,
    limit: int = 16,
) -> List[RankedProductItem]:
    """Retrieve supermarket products across diverse nutritional pillars and return them scored and ranked."""
    pillars = MEAL_SLOT_PILLARS.get(slot_name.lower(), [["food", "protein", "healthy"]])

    # If user provided specific food preferences, query those as well
    user_prefs = [w.strip() for w in profile.food_preferences.split(",") if len(w.strip()) > 2]

    candidates_map: Dict[str, EvidenceObject] = {}

    for pillar_idx, pillar_queries in enumerate(pillars):
        pillar_candidates = 0
        queries_to_try = pillar_queries[:3]
        if user_prefs and pillar_idx == 0:
            queries_to_try = [user_prefs[0]] + queries_to_try

        for q in queries_to_try:
            found = product_repo.search(query=q, limit=6)
            for p in found:
                if not _is_condiment_or_non_meal(p):
                    candidates_map[p.product_id] = p
                    pillar_candidates += 1

        # If local database has very few items for this pillar, fetch from Open Food Facts via Retrieval Service
        if pillar_candidates < 2 and pillar_queries:
            fallback_query = pillar_queries[0]
            try:
                req = RetrievalRequest(
                    trace_id=f"diet-retrieval-{slot_name}-p{pillar_idx}",
                    query=fallback_query,
                    intent="diet_planning",
                )
                res = retrieval_service(req)
                for cand in res.candidates:
                    if not _is_condiment_or_non_meal(cand):
                        candidates_map[cand.product_id] = cand
            except Exception as e:
                logger.warning(f"Fallback retrieval for '{fallback_query}' failed: {e}")

    # Rank all candidate products
    ranked: List[RankedProductItem] = []
    for p in candidates_map.values():
        if _is_condiment_or_non_meal(p):
            continue

        score, breakdown = score_product(p, profile, targets, meal_slot=slot_name)
        # Exclude products hit with heavy allergen penalties
        if breakdown.get("allergen_penalty", 0.0) >= 5.0:
            continue

        group = classify_food_group(p)

        ranked.append(
            RankedProductItem(
                product_id=p.product_id,
                name=p.name,
                brand=p.brand,
                barcode=p.barcode,
                categories=p.categories,
                ingredients_text=p.ingredients_text,
                allergens=p.allergens,
                nutrition=p.nutrition,
                score=score,
                score_breakdown=breakdown,
                safety_status="SUITABLE",
                safety_findings=[],
                food_group=group,
            )
        )

    # Sort descending by final score
    ranked.sort(key=lambda x: x.score, reverse=True)
    return ranked[:limit]
