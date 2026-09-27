"""Open Food Facts API Source Adapter.

Implements ProductSource interface to fetch, normalize, and cache packaged food
evidence from the Open Food Facts REST API.
"""

import logging
import time
from typing import Any
import httpx

from backend.app.agents.agent_stubs import EvidenceObject
from backend.app.sources.base import ProductSource

logger = logging.getLogger(__name__)

OFF_BARCODE_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
OFF_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
USER_AGENT = "EviBiteAI - WebAnalyticsAssignment - Version 1.0 (contact: student@univ.ac.lk)"


class OpenFoodFactsSource(ProductSource):
    """ProductSource implementation targeting Open Food Facts public API."""

    def __init__(self, cache_ttl_seconds: int = 3600, timeout_seconds: float = 6.0):
        self.cache_ttl = cache_ttl_seconds
        self.timeout = timeout_seconds
        self._cache: dict[str, tuple[float, Any]] = {}
        self.headers = {"User-Agent": USER_AGENT}


    def _get_from_cache(self, key: str) -> Any | None:
        if key in self._cache:
            created_at, val = self._cache[key]
            if time.time() - created_at < self.cache_ttl:
                return val
            else:
                del self._cache[key]
        return None

    def _set_in_cache(self, key: str, val: Any) -> None:
        self._cache[key] = (time.time(), val)

    def get_by_barcode(self, barcode: str) -> EvidenceObject | None:
        clean_code = "".join(c for c in barcode if c.isdigit())
        if not clean_code:
            return None

        cache_key = f"barcode:{clean_code}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        url = OFF_BARCODE_URL.format(barcode=clean_code)
        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == 1 and "product" in data:
                        evidence = self._normalize_product(data["product"])
                        self._set_in_cache(cache_key, evidence)
                        return evidence
        except Exception as e:
            logger.warning(f"Open Food Facts barcode lookup failed for {clean_code}: {e}")

        return None

    def search(
        self,
        query: str,
        category: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[EvidenceObject]:
        query_str = query.strip()
        if not query_str and not category:
            return []

        search_term = query_str
        if category and category.lower() not in query_str.lower():
            search_term = f"{category} {query_str}".strip()

        cache_key = f"search:{search_term.lower()}:{limit}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        params = {
            "action": "process",
            "json": "true",
            "search_terms": search_term,
            "page_size": min(limit, 20),
            "fields": (
                "code,product_name,product_name_en,brands,categories,categories_tags,"
                "ingredients_text,ingredients_text_en,allergens,allergens_tags,nutriments"
            ),
        }

        candidates: list[EvidenceObject] = []
        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = client.get(OFF_SEARCH_URL, params=params)
                if response.status_code == 200:
                    data = response.json()
                    products = data.get("products", [])
                    for raw in products:
                        ev = self._normalize_product(raw)
                        candidates.append(ev)

                    if candidates:
                        self._set_in_cache(cache_key, candidates)
                        return candidates
        except Exception as e:
            logger.warning(f"Open Food Facts search failed for '{search_term}': {e}")

        return candidates

    def _normalize_product(self, raw: dict[str, Any]) -> EvidenceObject:
        code = str(raw.get("code") or raw.get("_id") or "unknown-barcode")
        name = (
            raw.get("product_name")
            or raw.get("product_name_en")
            or raw.get("product_name_fr")
            or "Unknown Packaged Product"
        )
        brand = raw.get("brands") or None

        raw_categories = raw.get("categories_tags") or []
        if isinstance(raw_categories, str):
            raw_categories = [c.strip() for c in raw_categories.split(",") if c.strip()]
        categories = [
            c.replace("en:", "").replace("-", " ").strip()
            for c in raw_categories
            if isinstance(c, str)
        ]
        if not categories and raw.get("categories"):
            cats_str = str(raw["categories"])
            categories = [c.strip().lower() for c in cats_str.split(",") if c.strip()]

        ingredients_text = (
            raw.get("ingredients_text")
            or raw.get("ingredients_text_en")
            or raw.get("ingredients_text_fr")
            or None
        )

        # Normalize allergens
        allergens: list[str] = []
        raw_allergens = raw.get("allergens_tags") or raw.get("allergens_hierarchy") or []
        if isinstance(raw_allergens, str):
            raw_allergens = [a.strip() for a in raw_allergens.split(",") if a.strip()]

        for alg in raw_allergens:
            if isinstance(alg, str) and alg:
                clean_alg = alg.replace("en:", "").replace("-", " ").replace("_", " ").strip().lower()
                if clean_alg and clean_alg not in allergens:
                    allergens.append(clean_alg)

        if not allergens and raw.get("allergens"):
            alg_str = str(raw["allergens"])
            for part in alg_str.split(","):
                clean = part.replace("en:", "").strip().lower()
                if clean and clean not in allergens:
                    allergens.append(clean)

        # Extract nutrition
        nutriments = raw.get("nutriments") or {}
        nutrition = self._extract_nutrition(nutriments)

        # Calculate completeness
        completeness = self._calculate_completeness(name, ingredients_text, allergens, nutrition)

        return EvidenceObject(
            product_id=f"off-{code}",
            name=name,
            brand=brand,
            barcode=code if code != "unknown-barcode" else None,
            categories=categories,
            ingredients_text=ingredients_text,
            allergens=allergens,
            nutrition=nutrition,
            completeness=completeness,
            source="open_food_facts",
        )

    def _extract_nutrition(self, nutriments: dict[str, Any]) -> dict[str, Any]:
        nutrition: dict[str, Any] = {}

        def _get_val(*keys: str) -> float | None:
            for k in keys:
                val = nutriments.get(k)
                if val is not None:
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        pass
            return None

        sugars = _get_val("sugars_100g", "sugars_value", "sugars")
        if sugars is not None:
            nutrition["sugars_g_100g"] = round(sugars, 2)

        protein = _get_val("proteins_100g", "proteins_value", "proteins", "protein_100g")
        if protein is not None:
            nutrition["protein_g_100g"] = round(protein, 2)

        fat = _get_val("fat_100g", "fat_value", "fat")
        if fat is not None:
            nutrition["fat_g_100g"] = round(fat, 2)

        sat_fat = _get_val("saturated-fat_100g", "saturated-fat_value", "saturated_fat_100g")
        if sat_fat is not None:
            nutrition["saturated_fat_g_100g"] = round(sat_fat, 2)

        energy = _get_val("energy-kcal_100g", "energy-kcal_value", "energy-kcal", "energy_100g")
        if energy is not None:
            nutrition["energy_kcal_100g"] = round(energy, 2)

        sodium = _get_val("sodium_100g", "sodium_value", "sodium")
        if sodium is not None:
            nutrition["sodium_mg_100g"] = round(sodium * 1000, 2) if sodium < 10 else round(sodium, 2)

        salt = _get_val("salt_100g", "salt_value", "salt")
        if salt is not None:
            nutrition["salt_g_100g"] = round(salt, 2)

        fiber = _get_val("fiber_100g", "fiber_value", "fiber")
        if fiber is not None:
            nutrition["fiber_g_100g"] = round(fiber, 2)

        return nutrition

    def _calculate_completeness(
        self,
        name: str,
        ingredients_text: str | None,
        allergens: list[str],
        nutrition: dict[str, Any],
    ) -> float:
        score = 0.0
        # Product name present (0.25)
        if name and name != "Unknown Packaged Product":
            score += 0.25

        # Ingredients text present (0.35)
        if ingredients_text and len(ingredients_text.strip()) > 5:
            score += 0.35

        # Allergens or explicit zero/list (0.15)
        if allergens or ingredients_text:
            score += 0.15

        # Key nutrition values present (0.25 total - 0.05 each for 5 key nutrients)
        key_nutrients = ["sugars_g_100g", "protein_g_100g", "fat_g_100g", "energy_kcal_100g", "sodium_mg_100g"]
        present_count = sum(1 for k in key_nutrients if k in nutrition and nutrition[k] is not None)
        score += (present_count / len(key_nutrients)) * 0.25

        return round(min(score, 1.0), 2)
