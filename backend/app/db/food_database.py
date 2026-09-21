"""Curated Local Food Database Module.

Provides instant, rich product evidence objects for popular supermarket food items,
dairy products, cereals, snacks, beverages, and allergen/dietary categories.
Serves as the primary instant-response database layer alongside Open Food Facts API.
"""

from typing import Any
from backend.app.agents.agent_stubs import EvidenceObject


FOOD_DATABASE: list[EvidenceObject] = [
    # -------------------------------------------------------------
    # MILK & DAIRY PRODUCTS
    # -------------------------------------------------------------
    EvidenceObject(
        product_id="db-milk-whole-dairy",
        name="Anchor Full Cream Whole Milk",
        brand="Anchor",
        barcode="9410001000101",
        categories=["dairy", "milk", "beverages"],
        ingredients_text="Pasteurised whole cow's milk, vitamin D3.",
        allergens=["milk", "lactose", "dairy"],
        nutrition={
            "sugars_g_100g": 4.7,
            "protein_g_100g": 3.3,
            "fat_g_100g": 3.6,
            "saturated_fat_g_100g": 2.3,
            "energy_kcal_100g": 64.0,
            "sodium_mg_100g": 44.0,
            "calcium_mg_100g": 120.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-milk-oat-oatly",
        name="Oatly Barista Edition Oat Milk",
        brand="Oatly",
        barcode="7350037330723",
        categories=["plant-based milk", "beverages", "vegan"],
        ingredients_text="Oat base (water, oats 10%), rapeseed oil, dipotassium phosphate, calcium carbonate, calcium phosphates, iodised salt, vitamins (D2, riboflavin, B12).",
        allergens=["oats", "gluten"],
        nutrition={
            "sugars_g_100g": 3.4,
            "protein_g_100g": 1.1,
            "fat_g_100g": 3.0,
            "saturated_fat_g_100g": 0.3,
            "energy_kcal_100g": 59.0,
            "sodium_mg_100g": 40.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-milk-almond-breeze",
        name="Almond Breeze Unsweetened Almond Milk",
        brand="Blue Diamond",
        barcode="041570054060",
        categories=["plant-based milk", "beverages", "vegan", "dairy-free"],
        ingredients_text="Almond milk (filtered water, almonds), calcium carbonate, sea salt, potassium citrate, sunflower lecithin, gellan gum, natural flavor, vitamin A palmitate, vitamin D2, D-alpha-tocopherol (vitamin E).",
        allergens=["almonds", "tree nuts", "nuts"],
        nutrition={
            "sugars_g_100g": 0.0,
            "protein_g_100g": 0.6,
            "fat_g_100g": 1.1,
            "saturated_fat_g_100g": 0.1,
            "energy_kcal_100g": 13.0,
            "sodium_mg_100g": 70.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-dairy-greek-yogurt",
        name="Chobani Plain Whole Milk Greek Yogurt",
        brand="Chobani",
        barcode="894700010023",
        categories=["dairy", "yogurt", "greek yogurt"],
        ingredients_text="Cultured pasteurized whole milk, live active yogurt cultures (S. thermophilus, L. bulgaricus, L. acidophilus, Bifidus, L. casei).",
        allergens=["milk", "dairy", "lactose"],
        nutrition={
            "sugars_g_100g": 3.8,
            "protein_g_100g": 9.0,
            "fat_g_100g": 4.5,
            "saturated_fat_g_100g": 3.0,
            "energy_kcal_100g": 93.0,
            "sodium_mg_100g": 35.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-dairy-cheddar-cheese",
        name="Cathedral City Mature Cheddar Cheese",
        brand="Cathedral City",
        barcode="5020205001012",
        categories=["dairy", "cheese"],
        ingredients_text="Pasteurised cow's milk, salt, starter culture, vegetarian rennet.",
        allergens=["milk", "dairy", "lactose"],
        nutrition={
            "sugars_g_100g": 0.1,
            "protein_g_100g": 25.4,
            "fat_g_100g": 34.9,
            "saturated_fat_g_100g": 21.7,
            "energy_kcal_100g": 416.0,
            "sodium_mg_100g": 720.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-condensed-milk-nestle",
        name="Nestlé Sweetened Condensed Milk",
        brand="Nestlé",
        barcode="7613032123456",
        categories=["dairy", "milk", "sweetener"],
        ingredients_text="Whole milk, sugar. Contains 8% milk fat, 20% milk solids non-fat.",
        allergens=["milk", "lactose", "dairy"],
        nutrition={
            "sugars_g_100g": 55.4,
            "protein_g_100g": 7.9,
            "fat_g_100g": 8.7,
            "energy_kcal_100g": 331.0,
            "sodium_mg_100g": 100.0,
        },
        completeness=1.0,
        source="local_database",
    ),

    # -------------------------------------------------------------
    # CHOCOLATES, SPREADS & BISCUITS
    # -------------------------------------------------------------
    EvidenceObject(
        product_id="db-nutella-original",
        name="Nutella Hazelnut Spread",
        brand="Ferrero",
        barcode="3017620422003",
        categories=["spreads", "chocolate", "hazelnut"],
        ingredients_text="Sugar, palm oil, hazelnuts (13%), skimmed milk powder (8.7%), fat-reduced cocoa (7.4%), emulsifier: lecithins (soy), vanillin.",
        allergens=["hazelnut", "tree nuts", "nuts", "milk", "lactose", "soy"],
        nutrition={
            "sugars_g_100g": 56.3,
            "protein_g_100g": 6.3,
            "fat_g_100g": 30.9,
            "saturated_fat_g_100g": 10.6,
            "energy_kcal_100g": 539.0,
            "sodium_mg_100g": 42.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-nutella-plant-based",
        name="Nutella Plant-Based Vegan Spread",
        brand="Ferrero",
        barcode="8000500412345",
        categories=["spreads", "chocolate", "vegan"],
        ingredients_text="Sugar, palm oil, hazelnuts (13%), chickpeas, rice syrup powder, fat-reduced cocoa powder (7.4%), emulsifier: lecithins (soy), salt, vanillin.",
        allergens=["hazelnut", "tree nuts", "nuts", "soy"],
        nutrition={
            "sugars_g_100g": 45.0,
            "protein_g_100g": 5.2,
            "fat_g_100g": 31.0,
            "saturated_fat_g_100g": 9.8,
            "energy_kcal_100g": 520.0,
            "sodium_mg_100g": 50.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-cadbury-dairy-milk",
        name="Cadbury Dairy Milk Chocolate",
        brand="Cadbury",
        barcode="7622210001010",
        categories=["chocolate", "sweets", "confectionery"],
        ingredients_text="Milk, sugar, cocoa butter, cocoa mass, vegetable fats (palm, shea), emulsifiers (E442, E476), flavourings.",
        allergens=["milk", "lactose", "dairy"],
        nutrition={
            "sugars_g_100g": 56.0,
            "protein_g_100g": 7.3,
            "fat_g_100g": 30.5,
            "saturated_fat_g_100g": 18.5,
            "energy_kcal_100g": 534.0,
            "sodium_mg_100g": 95.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-kitkat-four-finger",
        name="KitKat 4 Finger Milk Chocolate Wafers",
        brand="Nestlé",
        barcode="5000189974567",
        categories=["chocolate", "wafers", "biscuits"],
        ingredients_text="Sugar, wheat flour (contains calcium, iron, thiamin and niacin), milk powders (whole and skimmed), cocoa mass, cocoa butter, vegetable fats (palm, shea, mango kernel, sal), butterfat (milk), emulsifier (lecithins), yeast, raising agent (sodium bicarbonate), whey powder (milk).",
        allergens=["wheat", "gluten", "milk", "lactose", "dairy", "soy"],
        nutrition={
            "sugars_g_100g": 49.6,
            "protein_g_100g": 6.9,
            "fat_g_100g": 24.3,
            "saturated_fat_g_100g": 13.6,
            "energy_kcal_100g": 502.0,
            "sodium_mg_100g": 90.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-oreo-original",
        name="Oreo Original Chocolate Sandwich Biscuits",
        brand="Oreo",
        barcode="7622300315485",
        categories=["biscuits", "snacks", "vegan"],
        ingredients_text="Wheat flour, sugar, palm oil, rapeseed oil, fat-reduced cocoa powder 4.3 %, wheat starch, glucose-fructose syrup, raising agents (ammonium carbonates, potassium carbonates, sodium carbonates), salt, emulsifier (soy lecithins), acidity regulator (sodium hydroxide), flavouring.",
        allergens=["wheat", "gluten", "soy"],
        nutrition={
            "sugars_g_100g": 38.0,
            "protein_g_100g": 5.2,
            "fat_g_100g": 20.0,
            "saturated_fat_g_100g": 5.4,
            "energy_kcal_100g": 474.0,
            "sodium_mg_100g": 290.0,
        },
        completeness=1.0,
        source="local_database",
    ),

    # -------------------------------------------------------------
    # CEREALS & BREAKFAST
    # -------------------------------------------------------------
    EvidenceObject(
        product_id="db-cheerios-honey-oats",
        name="Cheerios Honey & Whole Grain Oats Cereal",
        brand="Nestlé",
        barcode="7613035654321",
        categories=["cereals", "breakfasts"],
        ingredients_text="Whole grain oat flour (28.1%), whole grain wheat (28.1%), sugar, whole grain barley flour (17.1%), wheat starch, honey (3.8%), inverted sugar syrup, salt, tripotassium phosphate, vitamin E.",
        allergens=["oats", "wheat", "barley", "gluten"],
        nutrition={
            "sugars_g_100g": 9.3,
            "protein_g_100g": 8.4,
            "fat_g_100g": 3.8,
            "saturated_fat_g_100g": 0.8,
            "energy_kcal_100g": 382.0,
            "sodium_mg_100g": 140.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-special-k-original",
        name="Special K Original Low Fat Cereal",
        brand="Kellogg's",
        barcode="5000167032104",
        categories=["cereals", "breakfasts"],
        ingredients_text="Rice (39%), whole wheat (31%), sugar, barley (7.5%), malted barley flour, salt, malt flavouring, vitamins (niacin, iron, B6, B2, B1, folic acid, B12).",
        allergens=["wheat", "barley", "gluten"],
        nutrition={
            "sugars_g_100g": 14.0,
            "protein_g_100g": 14.0,
            "fat_g_100g": 1.5,
            "saturated_fat_g_100g": 0.3,
            "energy_kcal_100g": 375.0,
            "sodium_mg_100g": 350.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-weetabix-original",
        name="Weetabix 100% Whole Grain Cereal",
        brand="Weetabix",
        barcode="5010029000015",
        categories=["cereals", "breakfasts", "vegan", "low sugar"],
        ingredients_text="Whole wheat (95%), malted barley extract, sugar, salt, niacin, iron, riboflavin (B2), thiamin (B1), folic acid.",
        allergens=["wheat", "barley", "gluten"],
        nutrition={
            "sugars_g_100g": 4.4,
            "protein_g_100g": 12.0,
            "fat_g_100g": 2.0,
            "saturated_fat_g_100g": 0.6,
            "energy_kcal_100g": 362.0,
            "sodium_mg_100g": 100.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-kelloggs-corn-flakes",
        name="Kellogg's Original Corn Flakes",
        brand="Kellogg's",
        barcode="5000167000011",
        categories=["cereals", "breakfasts", "low fat"],
        ingredients_text="Maize, sugar, barley malt flavouring, salt, vitamins & minerals (niacin, iron, B6, B2, B1, folic acid, D, B12).",
        allergens=["barley", "gluten"],
        nutrition={
            "sugars_g_100g": 8.0,
            "protein_g_100g": 7.0,
            "fat_g_100g": 0.9,
            "saturated_fat_g_100g": 0.2,
            "energy_kcal_100g": 378.0,
            "sodium_mg_100g": 450.0,
        },
        completeness=1.0,
        source="local_database",
    ),

    # -------------------------------------------------------------
    # BEVERAGES & SOFT DRINKS
    # -------------------------------------------------------------
    EvidenceObject(
        product_id="db-coca-cola-zero",
        name="Coca-Cola Zero Sugar",
        brand="Coca-Cola",
        barcode="5449000214211",
        categories=["beverages", "soft drinks", "sugar-free", "vegan"],
        ingredients_text="Carbonated water, colour (caramel E150d), acid (phosphoric acid), sweeteners (aspartame, acesulfame K), natural flavourings, caffeine flavouring, acidity regulator (sodium citrates). Contains a source of phenylalanine.",
        allergens=[],
        nutrition={
            "sugars_g_100g": 0.0,
            "protein_g_100g": 0.0,
            "fat_g_100g": 0.0,
            "saturated_fat_g_100g": 0.0,
            "energy_kcal_100g": 0.3,
            "sodium_mg_100g": 8.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-pepsi-max",
        name="Pepsi Max Zero Sugar Cola",
        brand="Pepsi",
        barcode="5000177467890",
        categories=["beverages", "soft drinks", "sugar-free", "vegan"],
        ingredients_text="Carbonated water, colour (caramel E150d), sweeteners (aspartame, acesulfame K), acids (phosphoric acid, citric acid), flavourings (including caffeine), preservative (potassium sorbate).",
        allergens=[],
        nutrition={
            "sugars_g_100g": 0.0,
            "protein_g_100g": 0.0,
            "fat_g_100g": 0.0,
            "saturated_fat_g_100g": 0.0,
            "energy_kcal_100g": 0.6,
            "sodium_mg_100g": 10.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-tropicana-orange-juice",
        name="Tropicana Pure Premium Orange Juice",
        brand="Tropicana",
        barcode="5025970000123",
        categories=["beverages", "juice", "vegan", "gluten-free"],
        ingredients_text="100% pure squeezed orange juice from concentrate.",
        allergens=[],
        nutrition={
            "sugars_g_100g": 8.5,
            "protein_g_100g": 0.7,
            "fat_g_100g": 0.0,
            "saturated_fat_g_100g": 0.0,
            "energy_kcal_100g": 41.0,
            "sodium_mg_100g": 0.0,
        },
        completeness=1.0,
        source="local_database",
    ),

    # -------------------------------------------------------------
    # SAVOURY SNACKS & CHIPS
    # -------------------------------------------------------------
    EvidenceObject(
        product_id="db-lays-classic-salted",
        name="Lay's Classic Salted Potato Chips",
        brand="Lay's",
        barcode="028400064088",
        categories=["snacks", "chips", "crisps", "gluten-free", "vegan"],
        ingredients_text="Potatoes, vegetable oil (sunflower, corn, and/or canola oil), salt.",
        allergens=[],
        nutrition={
            "sugars_g_100g": 0.5,
            "protein_g_100g": 6.8,
            "fat_g_100g": 34.0,
            "saturated_fat_g_100g": 4.5,
            "energy_kcal_100g": 536.0,
            "sodium_mg_100g": 520.0,
        },
        completeness=1.0,
        source="local_database",
    ),
    EvidenceObject(
        product_id="db-doritos-nacho-cheese",
        name="Doritos Nacho Cheese Flavoured Tortilla Chips",
        brand="Doritos",
        barcode="028400064125",
        categories=["snacks", "chips", "tortilla"],
        ingredients_text="Corn, vegetable oil (corn, canola, and/or sunflower oil), maltodextrin (made from corn), salt, cheddar cheese (milk, cheese cultures, salt, enzymes), whey (milk), monosodium glutamate, buttermilk (milk), romano cheese (part-skim cow's milk, cheese cultures, salt, enzymes), whey protein concentrate (milk), onion powder, corn flour, natural and artificial flavor, dextrose, tomato powder, lactose (milk), spices, artificial color (yellow 6, yellow 5, red 40), lactic acid, citric acid, sugar, garlic powder, skim milk, red and green bell pepper powder, disodium inosinate, disodium guanylate.",
        allergens=["milk", "lactose", "dairy"],
        nutrition={
            "sugars_g_100g": 2.1,
            "protein_g_100g": 7.1,
            "fat_g_100g": 26.0,
            "saturated_fat_g_100g": 3.6,
            "energy_kcal_100g": 500.0,
            "sodium_mg_100g": 640.0,
        },
        completeness=1.0,
        source="local_database",
    ),
]


def search_local_database(
    query: str = "",
    category: str | None = None,
    allergens: list[str] | None = None,
    dietary: list[str] | None = None,
    limit: int = 10,
) -> list[EvidenceObject]:
    """Search local curated food database with smart text, category, allergen & dietary filters."""
    query_lower = query.lower().strip()
    category_lower = (category or "").lower().strip()
    allergens_lower = [a.lower().strip() for a in (allergens or [])]
    dietary_lower = [d.lower().strip() for d in (dietary or [])]

    results: list[tuple[float, EvidenceObject]] = []

    for item in FOOD_DATABASE:
        score = 0.0

        # Category match
        if category_lower:
            if any(category_lower in c for c in item.categories):
                score += 3.0

        # Direct name match
        if query_lower and query_lower in item.name.lower():
            score += 5.0
        elif query_lower:
            # Word intersection match
            q_words = set(query_lower.split())
            name_words = set(item.name.lower().split())
            ing_words = set((item.ingredients_text or "").lower().split())
            cat_words = set(" ".join(item.categories).lower().split())
            
            matches = len(q_words.intersection(name_words.union(cat_words)))
            if matches > 0:
                score += matches * 1.5

            if any(w in ing_words for w in q_words if len(w) > 3):
                score += 1.0

        # Allergen inclusion search (e.g. "products containing milk")
        if allergens_lower:
            for alg in allergens_lower:
                alg_singular = alg.rstrip("s")
                ing_text = (item.ingredients_text or "").lower()
                item_allergens = [a.lower() for a in item.allergens]

                if any(alg_singular in a for a in item_allergens) or alg_singular in ing_text:
                    score += 4.0

        # Dietary suitability search (e.g. "vegan snacks")
        if dietary_lower:
            for diet in dietary_lower:
                if diet in item.categories or diet in (item.ingredients_text or "").lower():
                    score += 3.0

        if score > 0.0 or (not query_lower and not category_lower and not allergens_lower and not dietary_lower):
            results.append((score, item))

    # Sort descending by score
    results.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in results[:limit]]
