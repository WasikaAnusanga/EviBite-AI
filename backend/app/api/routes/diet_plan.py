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


from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from backend.app.db.diet_plan_repository import diet_plan_repo


class SaveDietPlanRequest(BaseModel):
    user_id: str
    plan: Dict[str, Any]
    profile: Optional[Dict[str, Any]] = None
    plan_name: Optional[str] = None


@router.post(
    "/save",
    status_code=status.HTTP_201_CREATED,
    summary="Save User Diet Plan",
    description="Saves a generated diet plan to MongoDB for the specified user.",
)
def save_diet_plan_endpoint(request: SaveDietPlanRequest) -> Dict[str, Any]:
    try:
        saved = diet_plan_repo.save_plan(
            user_id=request.user_id,
            plan_data=request.plan,
            profile_data=request.profile,
            plan_name=request.plan_name,
        )
        return {"success": True, "plan": saved}
    except Exception as e:
        logger.error(f"Failed to save user diet plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save diet plan to database.",
        )


@router.get(
    "/user/{user_id}",
    summary="Get All Saved Diet Plans for User",
    description="Returns all previously saved diet plans for a specific user.",
)
def get_user_diet_plans_endpoint(user_id: str) -> Dict[str, Any]:
    try:
        plans = diet_plan_repo.get_user_plans(user_id=user_id)
        return {"user_id": user_id, "count": len(plans), "plans": plans}
    except Exception as e:
        logger.error(f"Failed to fetch diet plans for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch saved diet plans.",
        )


@router.get(
    "/{plan_id}",
    summary="Get Saved Diet Plan by ID",
    description="Returns full details of a saved diet plan by plan_id.",
)
def get_diet_plan_by_id_endpoint(plan_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    plan = diet_plan_repo.get_plan_by_id(plan_id=plan_id, user_id=user_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diet plan not found.",
        )
    return plan


@router.delete(
    "/{plan_id}",
    summary="Delete Saved Diet Plan",
    description="Deletes a saved diet plan from MongoDB.",
)
def delete_diet_plan_endpoint(plan_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    success = diet_plan_repo.delete_plan(plan_id=plan_id, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diet plan not found or could not be deleted.",
        )
    return {"success": True, "deleted_id": plan_id}
