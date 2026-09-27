"""Diet & Nutrition Planning API Routes.

Exposes endpoints for generating personalized diet and nutrition plans
grounded in the supermarket product database.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from backend.app.agents.diet_planning_agent.agent import diet_agent
from backend.app.agents.diet_planning_agent.schemas import DietProfile, GeneratedDietPlan
from backend.app.security.input_sanitization import sanitize_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/diet-plan", tags=["diet-plan"])


@router.post(
    "/generate",
    response_model=GeneratedDietPlan,
    status_code=status.HTTP_200_OK,
    summary="Generate Personalized Diet & Nutrition Plan",
    description=(
        "Accepts biometric data, goals, allergies, and dietary constraints, "
        "and uses the Diet & Nutrition Planning Agent to generate a grounded "
        "supermarket meal plan, macronutrient distribution, and grocery shopping list."
    ),
)
def generate_diet_plan_endpoint(profile: DietProfile) -> GeneratedDietPlan:
    """Generate a personalized diet plan based on user health profile."""
    try:
        # Sanitize free-text user inputs to prevent injection or invalid characters
        if profile.food_preferences:
            clean_pref = sanitize_message(profile.food_preferences)
            if not clean_pref.is_safe:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Food preferences input contains invalid characters. Please rephrase.",
                )
            profile.food_preferences = clean_pref.cleaned_message

        if profile.foods_to_avoid:
            clean_avoid = sanitize_message(profile.foods_to_avoid)
            if not clean_avoid.is_safe:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Foods to avoid input contains invalid characters. Please rephrase.",
                )
            profile.foods_to_avoid = clean_avoid.cleaned_message

        # Generate plan using autonomous agent
        plan = diet_agent.generate_plan(profile)
        return plan

    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(f"Validation error in diet plan generation: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Failed to generate diet plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating your diet plan. Please try again.",
        )
