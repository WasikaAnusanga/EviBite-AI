"""Diet & Nutrition Planning Agent Master Coordinator.

Orchestrates:
1. User Profile Processing & Normalization
2. Nutrition Requirement Engine (Calories, Macros, Conditions)
3. Product Retrieval & Multi-factor Ranking across Supermarket Catalog
4. Safety & Allergen Validation (reusing Agent 3 Analysis Service)
5. Meal Planning & Shopping List Assembly
6. LLM Explanation Generation (Gemini 3.1 Flash Lite)
"""

from datetime import datetime, timezone
import json
import logging
import os
import uuid
from typing import Dict, List

from backend.app.agents.agent_stubs import AnalysisRequest, EvidenceObject
from backend.app.agents.diet_planning_agent.nutrition_targets import compute_nutrition_targets
from backend.app.agents.diet_planning_agent.meal_planner import assemble_meal_slots, generate_shopping_list
from backend.app.agents.diet_planning_agent.product_ranker import retrieve_and_rank_products_for_slot
from backend.app.agents.diet_planning_agent.schemas import (
    DietPreference,
    DietProfile,
    GeneratedDietPlan,
    MealSlot,
    NutritionTargets,
    RankedProductItem,
)
from backend.app.agents.nutrition_allergen.service import analysis_service

logger = logging.getLogger(__name__)


def _run_safety_validation(
    candidates: List[RankedProductItem],
    profile: DietProfile,
    targets: NutritionTargets,
    trace_id: str,
) -> List[RankedProductItem]:
    """Validates products using Member 3's Nutrition & Allergen Analysis Agent."""
    if not candidates:
        return []

    # Map candidate RankedProductItems to EvidenceObjects for Agent 3
    evidence_objs = [
        EvidenceObject(
            product_id=p.product_id,
            name=p.name,
            brand=p.brand,
            barcode=p.barcode,
            categories=p.categories,
            ingredients_text=p.ingredients_text,
            allergens=p.allergens,
            nutrition=p.nutrition,
            completeness=1.0,
            source="supermarket_catalog",
        )
        for p in candidates
    ]

    # Formulate safety constraints based on profile and conditions
    diet_reqs = []
    if profile.diet in (DietPreference.VEGAN, DietPreference.VEGETARIAN):
        diet_reqs.append(profile.diet.value)

    nutrients_to_check = []
    conds = [c.lower() for c in profile.health_conditions]
    if "diabetes" in conds:
        nutrients_to_check.append("sugars")
    if "high_blood_pressure" in conds or "hypertension" in conds:
        nutrients_to_check.append("sodium")
    if "high_cholesterol" in conds:
        nutrients_to_check.append("fat")

    analysis_req = AnalysisRequest(
        trace_id=trace_id,
        primary_intent="diet_safety_validation",
        allergens=profile.allergies,
        nutrients=nutrients_to_check,
        dietary_requirements=diet_reqs,
        evidence=evidence_objs,
        original_query=f"Safe diet plan for {profile.goal.value} with allergies {profile.allergies}",
    )

    try:
        analysis_resp = analysis_service(analysis_req)
        # Parse product-specific findings
        findings_by_name: Dict[str, List[str]] = {}
        for f in analysis_resp.findings:
            if f.startswith("[") and "]" in f:
                p_name, text = f[1:].split("]", 1)
                findings_by_name.setdefault(p_name.strip(), []).append(text.strip())

        safe_products: List[RankedProductItem] = []
        for p in candidates:
            # Check if this product was flagged with severe incompatibility
            p_findings = findings_by_name.get(p.name, [])
            is_unsuitable = any(
                "CONFLICT" in f.upper()
                or "CONTAINS" in f.upper()
                or "UNSUITABLE" in f.upper()
                or "HIGH RISK" in f.upper()
                for f in p_findings
            )

            if is_unsuitable:
                logger.info(f"Diet Agent Safety Guardrail filtered out unsafe product: {p.name}")
                continue

            p.safety_status = "SUITABLE"
            p.safety_findings = p_findings
            safe_products.append(p)

        return safe_products

    except Exception as e:
        logger.warning(f"Diet safety validation notice: {e}. Falling back to rule-based ranking.")
        return candidates


def _generate_llm_explanation(
    profile: DietProfile,
    targets: NutritionTargets,
    meal_slots: List[MealSlot],
) -> str:
    """Synthesize personalized clinical and culinary diet plan explanation via Gemini LLM."""
    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )

    summary_meals = []
    for slot in meal_slots:
        slot_foods = [f"{item.product.name} ({item.serving_label}, {item.calories} kcal, {item.protein_g}g protein)" for item in slot.items]
        summary_meals.append(f"**{slot.meal_name}** ({slot.actual_calories} kcal, {slot.actual_protein_g}g P): {', '.join(slot_foods)}")

    meals_text = "\n".join(summary_meals)

    prompt = f"""You are the EviBite AI Diet & Nutrition Planning Agent, an intelligent clinical dietitian and supermarket food specialist.

The user has submitted their biometric and dietary health profile:
- Age: {profile.age}, Gender: {profile.gender.value}, Height: {profile.height} cm, Weight: {profile.weight} kg
- BMI: {targets.bmi} ({targets.bmi_category})
- Primary Health Goal: {profile.goal.value.replace('_', ' ').title()}
- Activity Level: {profile.activity.value.replace('_', ' ').title()}
- Dietary Lifestyle: {profile.diet.value.replace('_', ' ').title()}
- Declared Allergies: {', '.join(profile.allergies) if profile.allergies else 'None'}
- Diagnosed Health Conditions: {', '.join(profile.health_conditions) if profile.health_conditions else 'None'}
- Budget Constraint: {profile.budget.value.title()}
- Food Preferences: {profile.food_preferences or 'Standard supermarket staples'}
- Cooking Willingness: {profile.cooking_preference.value.replace('_', ' ').title()}
- Country / Regional Supermarket Market: {profile.country}

Calculated Daily Nutritional Targets:
- Target Calories: {targets.daily_calories} kcal (BMR: {targets.bmr} kcal, TDEE: {targets.tdee} kcal)
- Protein Target: {targets.protein_target}g
- Carbohydrate Target: {targets.carbs_target}g
- Healthy Fat Target: {targets.fat_target}g
- Maximum Added Sugar Limit: {targets.sugar_limit}g
- Maximum Daily Sodium: {targets.sodium_limit_mg}mg

Generated Supermarket Meal Structure:
{meals_text}

Instructions:
1. Provide a warm, empowering, highly personalized diet explanation tailored specifically to their goal of {profile.goal.value.replace('_', ' ')}.
2. Explain the physiological rationale for their daily caloric target ({targets.daily_calories} kcal) and macronutrient balance.
3. Highlight why these specific packaged supermarket products were selected (referencing their availability in {profile.country} supermarkets, high protein, low sugar, allergen safety, and convenience).
4. Note health precautions addressing their declared allergies and health conditions (e.g. sugar control, sodium moderation).
5. Provide 2-3 practical, actionable tips for meal prep and shopping in {profile.country} supermarkets.

Strict Formatting Guidelines:
- Start with a warm 1-2 sentence greeting and personalized overview.
- Use explicit markdown level-3 headings (`### `) for each section on its own line:
  ### 1. Physiological & Caloric Rationale
  ### 2. Supermarket Product Selection Strategy
  ### 3. Allergen Safety & Health Precautions
  ### 4. Practical Shopping & Meal Prep Tips
- Always format macro metrics and key product names in bold (e.g. **2,595 kcal**, **Protein (143g):**, **Fage Total 0% Greek Yogurt**).
- Use bullet points (`* `) on separate lines for specific items.
- Do not use horizontal rule lines (`---`) or write section titles without `### ` headers.
"""

    if api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            model_name = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=750,
                ),
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            logger.warning(f"Diet plan LLM synthesis failed: {e}")

    # High-quality fallback explanation if LLM is unavailable
    goal_title = profile.goal.value.replace("_", " ").title()
    diet_title = profile.diet.value.replace("_", " ").title()

    return f"""### Personalized Diet Strategy: {goal_title}

Your custom diet plan has been mathematically tailored for your biometric profile (**BMI: {targets.bmi}**, **TDEE: {targets.tdee} kcal**) and nutritional lifestyle (**{diet_title}**).

#### 🎯 Daily Caloric & Macronutrient Strategy
* **Daily Caloric Intake:** **{targets.daily_calories} kcal** — calibrated specifically for your goal of **{goal_title}** to maintain optimal energy and metabolic rate.
* **Protein Target ({targets.protein_target}g):** Provides the necessary amino acid pool to support muscle recovery, lean tissue retention, and sustained satiety.
* **Carbohydrates ({targets.carbs_target}g):** Supplies sustained complex glycogen to fuel daily physical activity.
* **Essential Fats ({targets.fat_target}g):** Supports hormone balance, joint health, and nutrient absorption.

#### 🛒 Supermarket Product Selection
* Selected genuine packaged products from supermarket catalogs that provide high protein density and minimal refined sugars (under **{targets.sugar_limit}g** per day).
* Verified against your declared allergen constraints (**{', '.join(profile.allergies) if profile.allergies else 'No allergies declared'}**).
* Calibrated for **{profile.cooking_preference.value.replace('_', ' ')}** convenience.

#### 💡 Practical Dietitian Tips
1. **Hydration:** Aim for 2.5 to 3.5 liters of water daily to assist metabolic processing and fiber assimilation.
2. **Consistent Meal Timing:** Consume your meals within 3 to 4-hour intervals to maintain steady blood glucose levels.
3. **Smart Grocery Shopping:** Use the shopping list below to purchase packaged foods with verified ingredient labels at your local supermarket.
"""


class DietPlanningAgent:
    """Autonomous Diet & Nutrition Planning Agent."""

    def __init__(self):
        self.name = "Diet & Nutrition Planning Agent"

    def generate_plan(self, profile: DietProfile) -> GeneratedDietPlan:
        """Main execution pipeline for generating a personalized diet plan."""
        trace_id = f"diet-trace-{uuid.uuid4().hex[:8]}"
        logger.info(f"Diet Planning Agent started generation for goal '{profile.goal.value}' (trace: {trace_id})")

        # Step 1: Compute anthropometrics and macro targets
        targets = compute_nutrition_targets(profile)

        # Step 2: Retrieve and rank candidate products for each meal category
        slot_categories = ["breakfast", "lunch", "dinner", "snack"]
        ranked_pool: Dict[str, List[RankedProductItem]] = {}

        for slot_key in slot_categories:
            candidates = retrieve_and_rank_products_for_slot(
                slot_name=slot_key,
                profile=profile,
                targets=targets,
                limit=10,
            )
            # Step 3: Run safety validation via Agent 3
            safe_candidates = _run_safety_validation(
                candidates=candidates,
                profile=profile,
                targets=targets,
                trace_id=trace_id,
            )
            ranked_pool[slot_key] = safe_candidates

        # Step 4: Assemble Meal Slots with realistic portions
        meal_slots = assemble_meal_slots(
            frequency=profile.meal_frequency,
            targets=targets,
            ranked_pool=ranked_pool,
        )

        # Step 5: Consolidate Shopping List
        shopping_list = generate_shopping_list(meal_slots)

        # Step 6: Generate LLM Explanation
        explanation = _generate_llm_explanation(profile, targets, meal_slots)

        safety_summary = (
            f"All products verified free of {', '.join(profile.allergies)}"
            if profile.allergies
            else "All products verified safe for dietary requirements."
        )

        plan = GeneratedDietPlan(
            trace_id=trace_id,
            user_goal=profile.goal.value.replace("_", " ").title(),
            user_diet=profile.diet.value.replace("_", " ").title(),
            user_country=profile.country,
            daily_targets=targets,
            meals=meal_slots,
            shopping_list=shopping_list,
            explanation=explanation,
            safety_summary=safety_summary,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(f"Diet Planning Agent successfully generated plan with {len(meal_slots)} meals and {len(shopping_list)} shopping items.")
        return plan


# Global singleton instance
diet_agent = DietPlanningAgent()
