import json
import os
from typing import Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

from backend.app.models.triage import (
    Constraint,
    Intent,
    ProductEntity,
)


class TriageLLMExtraction(BaseModel):
    primary_intent: Intent = Field(
        description="Primary intent of the user query."
    )
    secondary_intents: list[Intent] = Field(
        default_factory=list,
        description="Secondary intents if the query contains multiple intents (e.g. ['nutrition_query'] when asking both allergy and sugar content)."
    )
    products: list[ProductEntity] = Field(
        default_factory=list,
        description="Extracted product entities with name, brand, or barcode."
    )
    category: str | None = Field(
        default=None,
        description="Product category if mentioned (e.g. cereal, drink, beverage, snack, chocolate)."
    )
    allergens: list[str] = Field(
        default_factory=list,
        description="Canonical allergen names (e.g. peanut, milk, egg, soy, gluten, nuts)."
    )
    dietary_requirements: list[str] = Field(
        default_factory=list,
        description="Dietary requirements (e.g. vegan, vegetarian, dairy-free, gluten-free)."
    )
    nutrients: list[str] = Field(
        default_factory=list,
        description="Nutrients mentioned (e.g. sugars, protein, fat, sodium, energy)."
    )
    requested_fields: list[str] = Field(
        default_factory=list,
        description="Fields needed to answer the query (e.g. ingredients, allergens, sugars, protein, calories, dietary_suitability)."
    )
    constraints: list[Constraint] = Field(
        default_factory=list,
        description="Numerical thresholds or constraints extracted from query."
    )
    subtasks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Decomposed subtasks for multi-intent questions. Each dict should have 'intent', 'query_fragment', and 'target_fields'."
    )
    unsupported_requirements: list[str] = Field(
        default_factory=list,
        description="Any requests that cannot be answered from product food data (e.g. store live price, stock, aisle location)."
    )


EXTRACTION_PROMPT_TEMPLATE = """You are the Triage & Routing Agent for EviBite AI, a supermarket product intelligence assistant.
Your task is to analyze user queries about packaged food products and extract structured JSON matching the exact schema below.

CRITICAL INTENT STRINGS (YOU MUST USE ONLY THESE EXACT STRINGS FOR primary_intent AND secondary_intents):
- "product_search"
- "barcode_lookup"
- "allergen_query"
- "nutrition_query"
- "comparison"
- "dietary_query"
- "recommendation"
- "greeting"
- "unknown"

Rules:
1. Multi-intent queries: If the user asks about an allergy AND nutrition (e.g. "I have a peanut allergy. Can I eat Nutella and how much sugar does it have?"), set primary_intent to "allergen_query" and secondary_intents to ["nutrition_query"].
2. Greetings / Help / Thanks: If the user greets (e.g. "Hi", "Hello", "How are you"), asks what the system does ("Who are you?", "Help"), or thanks ("Thank you"), set primary_intent to "greeting".
3. Products array: Must be a list of objects with "name", "brand", or "barcode", e.g. [{"name": "Nutella"}].
4. Allergens: List canonical allergen names (e.g. ["peanut"]).
5. Nutrients: List canonical nutrient names (e.g. ["sugars"]).

Expected JSON format:
{
  "primary_intent": "allergen_query",
  "secondary_intents": ["nutrition_query"],
  "products": [{"name": "Nutella"}],
  "category": null,
  "allergens": ["peanut"],
  "dietary_requirements": [],
  "nutrients": ["sugars"],
  "requested_fields": ["allergens", "ingredients", "sugars"],
  "constraints": [],
  "subtasks": [
    {"intent": "allergen_query", "query_fragment": "peanut allergy check", "target_fields": ["allergens"]},
    {"intent": "nutrition_query", "query_fragment": "sugar content check", "target_fields": ["sugars"]}
  ],
  "unsupported_requirements": []
}

User query: "{query}"
"""


INTENT_MAP = {
    "greeting": Intent.GREETING,
    "hello": Intent.GREETING,
    "hi": Intent.GREETING,
    "help": Intent.GREETING,
    "thanks": Intent.GREETING,
    "allergy": Intent.ALLERGEN_QUERY,
    "allergen": Intent.ALLERGEN_QUERY,
    "check_allergy_safety": Intent.ALLERGEN_QUERY,
    "nutrition": Intent.NUTRITION_QUERY,
    "search": Intent.PRODUCT_SEARCH,
    "product": Intent.PRODUCT_SEARCH,
    "compare": Intent.COMPARISON,
    "diet": Intent.DIETARY_QUERY,
    "recommend": Intent.RECOMMENDATION,
}



def _normalize_intent(value: Any) -> Intent:
    if not isinstance(value, str):
        return Intent.UNKNOWN
    val = value.lower().strip()
    try:
        return Intent(val)
    except ValueError:
        for k, v in INTENT_MAP.items():
            if k in val:
                return v
        return Intent.UNKNOWN


def _normalize_llm_json(data: dict) -> dict:
    data["primary_intent"] = _normalize_intent(data.get("primary_intent"))
    
    sec_intents = data.get("secondary_intents", [])
    if isinstance(sec_intents, list):
        data["secondary_intents"] = [_normalize_intent(i) for i in sec_intents]

    products = data.get("products", [])
    norm_products = []
    if isinstance(products, list):
        for p in products:
            if isinstance(p, str):
                norm_products.append({"name": p})
            elif isinstance(p, dict):
                norm_products.append(p)
    data["products"] = norm_products
    return data


def extract_with_llm(query: str) -> TriageLLMExtraction | None:
    """Attempt LLM structured extraction using Gemini or OpenAI.

    Returns TriageLLMExtraction on success, or None if no API key is provided
    or if the LLM call fails.
    """
    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    if not api_key:
        return None

    # 1. Try Gemini via google-genai
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(query=query)

        for model_name in ["gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-1.5-flash"]:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                if response.text:
                    raw_text = response.text.strip()
                    if raw_text.startswith("```"):
                        raw_text = raw_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                    data = json.loads(raw_text)
                    normalized_data = _normalize_llm_json(data)
                    return TriageLLMExtraction.model_validate(normalized_data)
            except Exception:
                continue
    except Exception:
        pass

    # 2. Try OpenAI if OpenAI key or client is available
    if os.getenv("OPENAI_API_KEY"):
        try:
            import openai

            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            prompt = EXTRACTION_PROMPT_TEMPLATE.format(query=query)
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You extract structured data from food queries."},
                    {"role": "user", "content": prompt},
                ],
                response_format=TriageLLMExtraction,
                temperature=0.1,
            )
            return response.choices[0].message.parsed
        except Exception:
            pass

    return None
