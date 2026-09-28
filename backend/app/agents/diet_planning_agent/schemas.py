"""Pydantic Schemas for Diet & Nutrition Planning Agent."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class HealthGoal(str, Enum):
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    MUSCLE_GAIN = "muscle_gain"
    MAINTAIN_WEIGHT = "maintain_weight"
    GENERAL_HEALTH = "general_health"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT_ACTIVITY = "light_activity"
    MODERATE_ACTIVITY = "moderate_activity"
    VERY_ACTIVE = "very_active"
    ATHLETE = "athlete"


class DietPreference(str, Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    NON_VEGETARIAN = "non_vegetarian"
    KETO = "keto"
    HIGH_PROTEIN = "high_protein"
    LOW_CARB = "low_carb"


class BudgetLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MealFrequency(str, Enum):
    THREE_MEALS = "3_meals"
    FOUR_MEALS = "4_meals"
    FIVE_MEALS = "5_meals"
    SIX_MEALS = "6_meals"


class CookingPreference(str, Enum):
    NO_COOKING = "no_cooking"
    SIMPLE_COOKING = "simple_cooking"
    NORMAL_COOKING = "normal_cooking"


class DietProfile(BaseModel):
    """User profile input submitted from the frontend form."""
    age: int = Field(..., ge=10, le=120, description="Age in years")
    gender: Gender = Field(..., description="Gender (male, female, other)")
    height: float = Field(..., ge=80, le=250, description="Height in centimeters")
    weight: float = Field(..., ge=25, le=300, description="Weight in kilograms")
    goal: HealthGoal = Field(default=HealthGoal.MAINTAIN_WEIGHT, description="Primary health goal")
    activity: ActivityLevel = Field(default=ActivityLevel.MODERATE_ACTIVITY, description="Daily physical activity level")
    diet: DietPreference = Field(default=DietPreference.NON_VEGETARIAN, description="Dietary pattern")
    allergies: List[str] = Field(default_factory=list, description="Declared allergens to avoid")
    health_conditions: List[str] = Field(default_factory=list, description="Diagnosed health conditions")
    food_preferences: str = Field(default="", description="Preferred foods, e.g. 'Rice, chicken, berries'")
    foods_to_avoid: str = Field(default="", description="Disliked or excluded ingredients")
    budget: BudgetLevel = Field(default=BudgetLevel.MEDIUM, description="Budget constraint")
    meal_frequency: MealFrequency = Field(default=MealFrequency.THREE_MEALS, description="Daily meal count")
    cooking_preference: CookingPreference = Field(default=CookingPreference.NORMAL_COOKING, description="Cooking willingness")
    country: str = Field(default="United States", description="User's country or regional grocery market")


class NutritionTargets(BaseModel):
    """Calculated daily macronutrient and energy targets."""
    bmi: float
    bmi_category: str
    bmr: int
    tdee: int
    daily_calories: int
    protein_target: int
    carbs_target: int
    fat_target: int
    fiber_target: int = 28
    sugar_limit: int = 35
    sodium_limit_mg: int = 2300


class RankedProductItem(BaseModel):
    """Supermarket product scored and verified for the diet plan."""
    product_id: str
    name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    ingredients_text: Optional[str] = None
    allergens: List[str] = Field(default_factory=list)
    nutrition: Dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    safety_status: str = "SUITABLE"
    safety_findings: List[str] = Field(default_factory=list)
    food_group: str = "general"


class MealItem(BaseModel):
    """A specific food item assigned to a meal slot."""
    product: RankedProductItem
    serving_label: str
    portion_grams: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


class MealSlot(BaseModel):
    """A meal period (Breakfast, Lunch, Dinner, Snack) containing products."""
    meal_name: str
    target_calories: int
    actual_calories: float
    actual_protein_g: float
    actual_carbs_g: float
    actual_fat_g: float
    items: List[MealItem] = Field(default_factory=list)


class ShoppingListItem(BaseModel):
    """Recommended supermarket item on the final shopping list."""
    product_id: str
    name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    category: str
    quantity: str
    nutrition_highlights: Dict[str, Any] = Field(default_factory=dict)
    meal_slot: str


class GeneratedDietPlan(BaseModel):
    """Final output response returned by the Diet & Nutrition Planning Agent."""
    trace_id: str
    user_goal: str
    user_diet: str
    user_country: str = "United States"
    daily_targets: NutritionTargets
    meals: List[MealSlot] = Field(default_factory=list)
    shopping_list: List[ShoppingListItem] = Field(default_factory=list)
    explanation: str
    safety_summary: str
    timestamp: str
