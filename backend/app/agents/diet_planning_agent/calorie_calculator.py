"""Calorie and Energy Requirement Calculator.

Implements standard physiological formulas:
- BMI (Body Mass Index) & Category Classification
- BMR (Basal Metabolic Rate) via Mifflin-St Jeor Equation
- TDEE (Total Daily Energy Expenditure) based on physical activity factor
- Goal-oriented calorie deficits / surpluses with clinical safety bounds
"""

from typing import Tuple
from backend.app.agents.diet_planning_agent.schemas import ActivityLevel, Gender, HealthGoal


ACTIVITY_MULTIPLIERS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT_ACTIVITY: 1.375,
    ActivityLevel.MODERATE_ACTIVITY: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
    ActivityLevel.ATHLETE: 1.9,
}


def calculate_bmi(weight_kg: float, height_cm: float) -> Tuple[float, str]:
    """Calculate Body Mass Index (BMI) and corresponding WHO category."""
    if height_cm <= 0 or weight_kg <= 0:
        return 0.0, "Unknown"

    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25.0:
        category = "Normal weight"
    elif bmi < 30.0:
        category = "Overweight"
    else:
        category = "Obesity"

    return bmi, category


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: Gender) -> int:
    """Calculate Basal Metabolic Rate using the Mifflin-St Jeor Equation."""
    base = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age)
    if gender == Gender.MALE:
        bmr = base + 5
    elif gender == Gender.FEMALE:
        bmr = base - 161
    else:
        bmr = base - 78  # Gender-neutral midpoint

    return max(800, int(round(bmr)))


def calculate_tdee(bmr: int, activity: ActivityLevel) -> int:
    """Calculate Total Daily Energy Expenditure by applying the activity multiplier."""
    factor = ACTIVITY_MULTIPLIERS.get(activity, 1.55)
    return int(round(bmr * factor))


def calculate_daily_calories(tdee: int, goal: HealthGoal, gender: Gender) -> int:
    """Adjust TDEE based on the user's specific health and body composition goal.

    Enforces safe physiological minimums (1200 kcal/day for women, 1500 kcal/day for men).
    """
    safe_floor = 1200 if gender == Gender.FEMALE else 1500

    if goal == HealthGoal.WEIGHT_LOSS:
        # 20% deficit or ~500 kcal deficit
        target = int(round(tdee * 0.80))
        return max(safe_floor, target)

    if goal == HealthGoal.MUSCLE_GAIN:
        # 15% lean surplus for muscle synthesis (~300-450 kcal)
        target = int(round(tdee * 1.15))
        return target

    if goal == HealthGoal.WEIGHT_GAIN:
        # ~20% surplus
        target = int(round(tdee * 1.20))
        return target

    # Maintain Weight and General Health maintain energetic equilibrium
    return tdee
