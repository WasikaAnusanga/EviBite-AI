"""Meal Planning and Portion Allocation Engine.

Allocates daily caloric and macronutrient targets across user meal frequencies
(3, 4, 5, or 6 meals), maps ranked supermarket products to slots with realistic
portion sizes, and consolidates the grocery shopping list.
"""

from typing import Dict, List, Tuple
from backend.app.agents.diet_planning_agent.schemas import (
    MealFrequency,
    MealItem,
    MealSlot,
    NutritionTargets,
    RankedProductItem,
    ShoppingListItem,
)


# Caloric distribution proportions across different meal frequencies
SLOT_CONFIGS: Dict[MealFrequency, List[Tuple[str, float, str]]] = {
    MealFrequency.THREE_MEALS: [
        ("Breakfast", 0.30, "breakfast"),
        ("Lunch", 0.35, "lunch"),
        ("Dinner", 0.35, "dinner"),
    ],
    MealFrequency.FOUR_MEALS: [
        ("Breakfast", 0.25, "breakfast"),
        ("Lunch", 0.35, "lunch"),
        ("Snack", 0.15, "snack"),
        ("Dinner", 0.25, "dinner"),
    ],
    MealFrequency.FIVE_MEALS: [
        ("Breakfast", 0.25, "breakfast"),
        ("Morning Snack", 0.10, "snack"),
        ("Lunch", 0.30, "lunch"),
        ("Afternoon Snack", 0.10, "snack"),
        ("Dinner", 0.25, "dinner"),
    ],
    MealFrequency.SIX_MEALS: [
        ("Meal 1 (Breakfast)", 0.20, "breakfast"),
        ("Meal 2 (Mid-Morning)", 0.15, "snack"),
        ("Meal 3 (Lunch)", 0.20, "lunch"),
        ("Meal 4 (Afternoon)", 0.15, "snack"),
        ("Meal 5 (Dinner)", 0.20, "dinner"),
        ("Meal 6 (Evening)", 0.10, "snack"),
    ],
}


def _calculate_portion_grams(product: RankedProductItem, target_calories: int) -> Tuple[float, str]:
    """Determine realistic serving weight and descriptive label for a supermarket product."""
    energy_100g = float(product.nutrition.get("energy_kcal_100g") or 250.0)
    name_lower = product.name.lower()

    # Define sensible standard serving bounds by food classification
    if any(k in name_lower for k in ["milk", "beverage", "drink", "juice"]):
        portion = 250.0  # 1 cup / glass
        label = "250 ml (1 glass)"
    elif any(k in name_lower for k in ["yogurt", "greek yogurt"]):
        portion = 170.0  # standard single-serve pot
        label = "170 g (1 tub)"
    elif any(k in name_lower for k in ["oat", "cereal", "weetabix", "granola"]):
        portion = 60.0  # standard breakfast bowl
        label = "60 g serving"
    elif any(k in name_lower for k in ["bar", "protein bar"]):
        portion = 55.0  # standard bar
        label = "1 bar (55g)"
    elif any(k in name_lower for k in ["bread", "toast", "wrap", "tortilla"]):
        portion = 75.0  # 2 slices / 1 wrap
        label = "75 g (2 slices / 1 wrap)"
    elif any(k in name_lower for k in ["almond", "walnut", "nut", "seed", "peanut butter"]):
        portion = 30.0  # standard 1 oz palm serving
        label = "30 g (handful / 2 tbsp)"
    elif any(k in name_lower for k in ["cheese"]):
        portion = 35.0
        label = "35 g (slice)"
    else:
        # Default scaled portion: target ~40-60% of this meal slot's energy
        desired_cal = max(150, target_calories * 0.45)
        portion = round(min(250.0, max(40.0, (desired_cal / max(50.0, energy_100g)) * 100.0)), 0)
        label = f"{int(portion)} g serving"

    return portion, label


def create_meal_item(product: RankedProductItem, slot_target_cal: int) -> MealItem:
    """Build a MealItem with nutritional values calculated for its specific portion."""
    portion, label = _calculate_portion_grams(product, slot_target_cal)
    factor = portion / 100.0

    nutr = product.nutrition
    cal = round(float(nutr.get("energy_kcal_100g") or 0.0) * factor, 1)
    prot = round(float(nutr.get("protein_g_100g") or 0.0) * factor, 1)
    fat = round(float(nutr.get("fat_g_100g") or 0.0) * factor, 1)

    carbs_100g = nutr.get("carbohydrates_100g")
    if carbs_100g is None:
        kcal_100 = float(nutr.get("energy_kcal_100g") or 0.0)
        p_100 = float(nutr.get("protein_g_100g") or 0.0)
        f_100 = float(nutr.get("fat_g_100g") or 0.0)
        carbs_100g = max(0.0, (kcal_100 - (p_100 * 4 + f_100 * 9)) / 4.0)

    carbs = round(float(carbs_100g) * factor, 1)

    return MealItem(
        product=product,
        serving_label=label,
        portion_grams=portion,
        calories=cal,
        protein_g=prot,
        carbs_g=carbs,
        fat_g=fat,
    )


import re

def _get_product_stems(name: str) -> set:
    """Extract distinguishing keyword stems from a product name."""
    words = set(re.findall(r'[a-zA-Z]{3,}', name.lower()))
    ignore = {"original", "wholegrain", "whole", "grain", "natural", "organic", "pack", "serving", "style", "classic", "fresh", "free", "pure"}
    return {w for w in words if w not in ignore}


DAILY_MAX_GROUPS: Dict[str, int] = {
    "cereal_oats": 1,       # Max 1 oat/cereal meal per day (no eating oats all day!)
    "bakery_grains": 1,     # Max 1 bread/wrap per day
    "poultry_meat": 1,      # Max 1 chicken/poultry meal per day
    "fish_seafood": 1,      # Max 1 fish/tuna/salmon meal per day
    "starchy_carbs": 2,     # Rice/quinoa/potato (e.g. lunch and dinner)
    "fruits": 2,            # Fruit (e.g. morning and snack)
    "vegetables": 3,        # Greens & veggies
    "healthy_snacks": 2,    # Protein bars, rice cakes, dark chocolate
    "nuts_seeds": 1,        # Handful of nuts/seeds
    "eggs": 1,              # Eggs
    "plant_milk": 1,        # Almond/oat milk
    "dairy_protein": 1,     # Greek yogurt/cheese
    "junk_snacks": 0,       # Never recommend chips, crisps, or junk snacks in health diet plans
}


def assemble_meal_slots(
    frequency: MealFrequency,
    targets: NutritionTargets,
    ranked_pool: Dict[str, List[RankedProductItem]],
) -> List[MealSlot]:
    """Assemble all meal slots for the day with assigned products and aggregated totals."""
    slots_config = SLOT_CONFIGS.get(frequency, SLOT_CONFIGS[MealFrequency.THREE_MEALS])
    meal_slots: List[MealSlot] = []

    daily_used_product_ids = set()
    daily_used_stems = set()
    daily_group_counts: Dict[str, int] = {}

    for meal_name, cal_pct, category_key in slots_config:
        slot_target_cal = int(round(targets.daily_calories * cal_pct))
        candidates = ranked_pool.get(category_key, [])

        slot_items: List[MealItem] = []
        used_groups_in_meal = set()
        accumulated_cal = 0.0
        accumulated_prot = 0.0
        accumulated_carbs = 0.0
        accumulated_fat = 0.0

        items_needed = 2 if "snack" in category_key else 3

        # Pass 1: Strict food group diversity, daily group frequency caps, and no repeated title stems
        for candidate in candidates:
            if candidate.product_id in daily_used_product_ids:
                continue

            c_stems = _get_product_stems(candidate.name)
            if c_stems & daily_used_stems:
                continue

            c_group = getattr(candidate, "food_group", "general")
            # Enforce intra-meal diversity (no 2 items from same group in one meal)
            if c_group != "general" and c_group in used_groups_in_meal:
                continue

            # Enforce daily frequency limits (e.g., max 1 oat item per day)
            if c_group != "general" and daily_group_counts.get(c_group, 0) >= DAILY_MAX_GROUPS.get(c_group, 99):
                continue

            item = create_meal_item(candidate, slot_target_cal)
            slot_items.append(item)
            daily_used_product_ids.add(candidate.product_id)
            daily_used_stems.update(c_stems)
            if c_group != "general":
                used_groups_in_meal.add(c_group)
                daily_group_counts[c_group] = daily_group_counts.get(c_group, 0) + 1

            accumulated_cal += item.calories
            accumulated_prot += item.protein_g
            accumulated_carbs += item.carbs_g
            accumulated_fat += item.fat_g

            if len(slot_items) >= items_needed:
                break

        # Pass 2: If still needing items, relax daily stem check but keep food group diversity & daily group caps
        if len(slot_items) < items_needed:
            for candidate in candidates:
                if candidate.product_id in daily_used_product_ids:
                    continue
                c_group = getattr(candidate, "food_group", "general")
                if c_group != "general" and c_group in used_groups_in_meal:
                    continue
                if c_group != "general" and daily_group_counts.get(c_group, 0) >= DAILY_MAX_GROUPS.get(c_group, 99):
                    continue

                item = create_meal_item(candidate, slot_target_cal)
                slot_items.append(item)
                daily_used_product_ids.add(candidate.product_id)
                if c_group != "general":
                    used_groups_in_meal.add(c_group)
                    daily_group_counts[c_group] = daily_group_counts.get(c_group, 0) + 1

                accumulated_cal += item.calories
                accumulated_prot += item.protein_g
                accumulated_carbs += item.carbs_g
                accumulated_fat += item.fat_g

                if len(slot_items) >= items_needed:
                    break

        # Pass 3: If still needing items, borrow complementary item from remaining pools without violating daily group limits
        if len(slot_items) < items_needed:
            backup_candidates = ranked_pool.get("snack", []) + ranked_pool.get("dinner", []) + ranked_pool.get("lunch", []) + ranked_pool.get("breakfast", [])
            for candidate in backup_candidates:
                if candidate.product_id in daily_used_product_ids:
                    continue
                c_group = getattr(candidate, "food_group", "general")
                if c_group != "general" and c_group in used_groups_in_meal:
                    continue
                if c_group != "general" and daily_group_counts.get(c_group, 0) >= DAILY_MAX_GROUPS.get(c_group, 99):
                    continue

                item = create_meal_item(candidate, slot_target_cal)
                slot_items.append(item)
                daily_used_product_ids.add(candidate.product_id)
                if c_group != "general":
                    used_groups_in_meal.add(c_group)
                    daily_group_counts[c_group] = daily_group_counts.get(c_group, 0) + 1

                accumulated_cal += item.calories
                accumulated_prot += item.protein_g
                accumulated_carbs += item.carbs_g
                accumulated_fat += item.fat_g

                if len(slot_items) >= items_needed:
                    break

        meal_slots.append(
            MealSlot(
                meal_name=meal_name,
                target_calories=slot_target_cal,
                actual_calories=round(accumulated_cal, 1),
                actual_protein_g=round(accumulated_prot, 1),
                actual_carbs_g=round(accumulated_carbs, 1),
                actual_fat_g=round(accumulated_fat, 1),
                items=slot_items,
            )
        )

    return meal_slots


def generate_shopping_list(meal_slots: List[MealSlot]) -> List[ShoppingListItem]:
    """Consolidate all recommended items from the meal plan into a structured grocery shopping list."""
    shopping_items_map: Dict[str, ShoppingListItem] = {}

    for slot in meal_slots:
        for item in slot.items:
            pid = item.product.product_id
            if pid not in shopping_items_map:
                main_category = (
                    item.product.categories[0].title()
                    if item.product.categories
                    else "Supermarket Grocery"
                )
                shopping_items_map[pid] = ShoppingListItem(
                    product_id=pid,
                    name=item.product.name,
                    brand=item.product.brand,
                    barcode=item.product.barcode,
                    category=main_category,
                    quantity="1 package / weekly supply",
                    nutrition_highlights={
                        "energy_kcal": item.product.nutrition.get("energy_kcal_100g"),
                        "protein_g": item.product.nutrition.get("protein_g_100g"),
                        "sugars_g": item.product.nutrition.get("sugars_g_100g"),
                    },
                    meal_slot=slot.meal_name,
                )

    return list(shopping_items_map.values())
