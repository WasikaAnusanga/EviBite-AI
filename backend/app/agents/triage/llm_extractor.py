import json
import os
from typing import Any
from pydantic import BaseModel, Field

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
Your task is to analyze user queries about packaged food products and extract structured JSON matching the requested schema.

Available Intent classes:
- product_search: Questions about product details, ingredients, or general product queries.
- barcode_lookup: Exact barcode search.
- allergen_query: Questions asking about allergens, allergy safety, or "contains" questions.
- nutrition_query: Questions about nutrient values (sugars, protein, fat, calories, sodium, etc.).
- comparison: Queries comparing two or more products or asking which option has lower/higher nutrient values.
- dietary_query: Questions about dietary suitability (vegan, vegetarian, gluten-free, dairy-free).
- recommendation: Requests to recommend or suggest products matching constraints or preferences.
- unknown: Irrelevant or completely unsupported queries.

Rules:
1. Multi-intent queries: If the user asks about an allergy AND nutrition (e.g. "I have a peanut allergy. Can I eat Nutella and how much sugar does it have?"), set primary_intent to "allergen_query" and secondary_intents to ["nutrition_query"].
2. Decompose multi-intent queries into subtasks array with "intent", "query_fragment", and "target_fields".
3. Product entities: Extract exact product names (e.g. "Nutella", "Coca-Cola Zero").
4. Canonical terms: Normalize allergens to lowercase canonical names (peanut, milk, egg, soy, gluten, nuts). Normalize nutrients to lowercase canonical names (sugars, protein, fat, sodium, energy).

User query: "{query}"
"""


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

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TriageLLMExtraction,
                temperature=0.1,
            ),
        )
        if response.text:
            data = json.loads(response.text)
            return TriageLLMExtraction.model_validate(data)
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
