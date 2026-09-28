"""Macronutrient & Micronutrient Target Generator.

Calculates target grams and ratios for Protein, Carbohydrates, and Fats
tailored to user goals, body weight, dietary patterns (e.g. Keto, High Protein),
and clinical health conditions (e.g. Diabetes, Hypertension).
"""

from backend.app.agents.diet_planning_agent.calorie_calculator import (
    calculate_bmi,
    calculate_bmr,
    calculate_daily_calories,
    calculate_tdee,
)
from backend.app.agents.diet_planning_agent.schemas import (
    DietPreference,
    DietProfile,
    HealthGoal,
    NutritionTargets,
)


def compute_nutrition_targets(profile: DietProfile) -> NutritionTargets:
    """Compute complete physiological and macronutrient target profile."""
    # 1. Anthropometric & Energetics
    bmi, bmi_category = calculate_bmi(profile.weight, profile.height)
    bmr = calculate_bmr(profile.weight, profile.height, profile.age, profile.gender)
    tdee = calculate_tdee(bmr, profile.activity)
    daily_calories = calculate_daily_calories(tdee, profile.goal, profile.gender)

    # 2. Macro distribution percentages (Protein %, Carbs %, Fat %)
    # Baseline defaults
    p_pct, c_pct, f_pct = 0.22, 0.50, 0.28

    if profile.diet == DietPreference.KETO:
        p_pct, c_pct, f_pct = 0.25, 0.05, 0.70
    elif profile.diet == DietPreference.LOW_CARB:
        p_pct, c_pct, f_pct = 0.30, 0.20, 0.50
    elif profile.diet == DietPreference.HIGH_PROTEIN:
        p_pct, c_pct, f_pct = 0.35, 0.40, 0.25
    elif profile.goal == HealthGoal.MUSCLE_GAIN:
        p_pct, c_pct, f_pct = 0.28, 0.47, 0.25
    elif profile.goal == HealthGoal.WEIGHT_LOSS:
        p_pct, c_pct, f_pct = 0.30, 0.42, 0.28
    elif profile.goal == HealthGoal.WEIGHT_GAIN:
        p_pct, c_pct, f_pct = 0.22, 0.53, 0.25

    # 3. Calculate target grams (Protein: 4 kcal/g, Carbs: 4 kcal/g, Fat: 9 kcal/g)
    protein_g = int(round((daily_calories * p_pct) / 4.0))
    carbs_g = int(round((daily_calories * c_pct) / 4.0))
    fat_g = int(round((daily_calories * f_pct) / 9.0))

    # Cross-check minimum protein requirement per kg bodyweight
    # Active/muscle goals require at least 1.6g - 2.0g/kg
    if profile.goal in (HealthGoal.MUSCLE_GAIN, HealthGoal.WEIGHT_LOSS):
        min_protein = int(round(profile.weight * 1.8))
        if protein_g < min_protein:
            protein_g = min_protein
            remaining_cal = max(500, daily_calories - (protein_g * 4))
            carbs_g = int(round((remaining_cal * 0.60) / 4.0))
            fat_g = int(round((remaining_cal * 0.40) / 9.0))

    # 4. Health Condition Adjustments
    conditions = [c.lower() for c in profile.health_conditions]
    fiber_target = 28
    sugar_limit = 35
    sodium_limit_mg = 2300

    if "diabetes" in conditions:
        sugar_limit = 20  # Tight sugar limitation for blood glycemic control
        fiber_target = 35  # Higher fiber for slower glucose absorption

    if "high_blood_pressure" in conditions or "hypertension" in conditions:
        sodium_limit_mg = 1500  # DASH diet sodium restriction

    if "high_cholesterol" in conditions:
        fiber_target = 35  # Soluble fiber helps lower LDL
        sugar_limit = 25

    return NutritionTargets(
        bmi=bmi,
        bmi_category=bmi_category,
        bmr=bmr,
        tdee=tdee,
        daily_calories=daily_calories,
        protein_target=protein_g,
        carbs_target=carbs_g,
        fat_target=fat_g,
        fiber_target=fiber_target,
        sugar_limit=sugar_limit,
        sodium_limit_mg=sodium_limit_mg,
    )
