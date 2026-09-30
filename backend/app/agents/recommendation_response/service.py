"""Recommendation & Response Agent service (Member 4).

Turns retrieved evidence + analysis into a grounded, user-facing answer.
"""

from backend.app.agents.agent_stubs import ResponseRequest, ResponseResponse

def _parse_direction(query: str, nutrient: str) -> str | None:
    """Look for 'less/low' or 'more/high' near a nutrient word in the query.
    Returns 'minimize', 'maximize', or None if no clear signal is found.
    """
    query_lower = query.lower()
    less_words = ["less", "low", "lower", "fewer", "reduced"]
    more_words = ["more", "high", "higher", "increased"]

    nutrient_lower = nutrient.lower()
    nutrient_singular = nutrient_lower.rstrip("s")  # "sugars" -> "sugar"
    nutrient_present = nutrient_lower in query_lower or nutrient_singular in query_lower

    if any(word in query_lower for word in less_words) and nutrient_present:
        return "minimize"
    if any(word in query_lower for word in more_words) and nutrient_present:
        return "maximize"
    return None


def _nutrient_field_name(nutrient: str) -> str | None:
    """Map a short nutrient word (from Triage) to the real EvidenceObject field name."""
    mapping = {
        "sugars": "sugars_g_100g",
        "sugar": "sugars_g_100g",
        "protein": "protein_g_100g",
        "fat": "fat_g_100g",
        "calories": "energy_kcal_100g",
        "energy": "energy_kcal_100g",
        "sodium": "sodium_mg_100g",
    }
    return mapping.get(nutrient.lower())


def rank_candidates(evidence: list, query: str, nutrients: list[str]) -> list:
    """Rank evidence candidates by how well they satisfy nutrient direction preferences
    extracted from the query. Candidates with no scorable preference keep their
    original (Retrieval-assigned) order.
    """
    if not nutrients or not evidence:
        return evidence

    # Figure out which fields matter and in which direction.
    directions: dict[str, str] = {}
    for nutrient in nutrients:
        field = _nutrient_field_name(nutrient)
        direction = _parse_direction(query, nutrient)
        if field and direction:
            directions[field] = direction

    if not directions:
        return evidence  # No usable direction signal — don't reorder blindly.

    def score(ev) -> float:
        total = 0.0
        counted = 0
        for field, direction in directions.items():
            value = ev.nutrition.get(field)
            if value is None:
                continue  # Missing data — don't guess, just skip this field.
            # Lower raw value = better for "minimize", higher = better for "maximize".
            total += (-value if direction == "minimize" else value)
            counted += 1
        # Candidates with no usable nutrition data for the requested fields
        # rank last, not first — missing data is not a reason to prefer them.
        return total if counted > 0 else float("-inf")

    return sorted(evidence, key=score, reverse=True)

import os
import json
import logging
from backend.app.agents.agent_stubs import ResponseRequest, ResponseResponse

logger = logging.getLogger(__name__)


def _generate_llm_response(
    query: str,
    evidence_list: list,
    findings: list[str],
    triage_status: str = "READY",
    chat_history: list[dict[str, str]] | None = None,
    user_diet_plan: dict | None = None,
) -> str | None:
    """Use Gemini LLM to synthesize a natural, intelligent, grounded answer with multi-turn conversation memory and user diet plan context."""
    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    if not api_key:
        return None

    evidence_summary = []
    for ev in evidence_list[:5]:
        evidence_summary.append({
            "name": ev.name,
            "brand": ev.brand,
            "ingredients": ev.ingredients_text,
            "allergens": ev.allergens,
            "nutrition_per_100g": ev.nutrition,
        })

    history_str = ""
    if chat_history:
        turns_fmt = []
        for turn in chat_history[-4:]:  # Last 4 turns
            role_label = "User" if turn.get("role") == "user" else "Assistant"
            turns_fmt.append(f"{role_label}: {turn.get('content')}")
        history_str = "\n".join(turns_fmt)

    is_doc_upload = "📄 [" in query or "Uploaded Recipe" in query or "Uploaded Document" in query
    is_asking_about_diet = any(
        w in query.lower() for w in ["diet plan", "my diet", "my plan", "my goals", "weight goal", "daily calories", "my macros", "fit in my plan", "fits my plan"]
    )

    # Format user's active diet plan context ONLY if user explicitly asked or if it's NOT a document upload
    diet_plan_str = ""
    if user_diet_plan and (is_asking_about_diet or not is_doc_upload):
        daily = user_diet_plan.get("daily_targets") or {}
        profile = user_diet_plan.get("profile") or {}
        meals = user_diet_plan.get("meals") or []
        shopping = user_diet_plan.get("shopping_list") or []

        meal_items = []
        for m in meals:
            p_names = [f"{it.get('name')} ({it.get('calories')} kcal)" for it in m.get("items", [])]
            meal_items.append(f"  • {m.get('meal_name')}: {', '.join(p_names)} (Target: {m.get('target_calories')} kcal)")

        shop_sample = [f"{s.get('name')} ({s.get('quantity')})" for s in shopping[:8]]

        diet_plan_str = f"""
User's Active Personalized Diet Plan (Saved in Profile):
- Plan Title: {user_diet_plan.get('title', 'Personalized Blueprint')}
- Goal: {user_diet_plan.get('user_goal')}
- Dietary Lifestyle: {user_diet_plan.get('user_diet')}
- Regional Market: {user_diet_plan.get('user_country', 'Global')}
- Daily Target Energy: {daily.get('daily_calories')} kcal/day
- Target Macronutrients: Protein: {daily.get('protein_target')}g | Carbs: {daily.get('carbs_target')}g | Fat: {daily.get('fat_target')}g
- Biometrics: BMI: {daily.get('bmi')} ({daily.get('bmi_category')}) | BMR: {daily.get('bmr')} kcal | TDEE: {daily.get('tdee')} kcal
- Declared Allergies: {', '.join(profile.get('allergies', [])) if profile.get('allergies') else 'None'}
- Medical Considerations: {', '.join(profile.get('medical_conditions', [])) if profile.get('medical_conditions') else 'None'}
- Planned Daily Meals:
{chr(10).join(meal_items) if meal_items else '  (None listed)'}
- Key Grocery Items: {', '.join(shop_sample) if shop_sample else 'None'}
"""

    prompt = f"""You are EviBite AI, an intelligent, friendly supermarket food product, nutrition, and diet planning assistant.

{diet_plan_str if diet_plan_str else "User Diet Plan Context: (Not applicable for this specific query.)"}

Recent Conversation History:
{history_str if history_str else "(New Conversation)"}

Current User Query: "{query}"
Triage Status: {triage_status}

Retrieved Product Evidence:
{json.dumps(evidence_summary, indent=2)}

Safety Analysis Findings:
{json.dumps(findings, indent=2)}

Instructions:
1. STRICT FOCUS FOR UPLOADED FILES/DOCUMENTS:
   - If the user uploaded a document or PDF (query contains '📄 [Uploaded Recipe PDF...]'), focus EXCLUSIVELY on reading, parsing, and answering the user's specific request about that uploaded file.
   - Do NOT talk about, mention, or bring up the user's diet plan, weight goals, daily calorie targets, or personal profile unless the user specifically asked about their diet plan in their prompt.
2. User Diet Plan Awareness:
   - ONLY reference or analyze the user's saved diet plan IF the user explicitly asks about their diet plan, calories, macros, or asks whether a food fits into their diet plan.
3. Multi-turn conversation memory: Pay attention to prior turns! If the user uses pronouns like "its", "it", "this product", or asks follow-ups, refer directly to the product or document discussed in previous turns.
4. Directly answer the user's specific question clearly with bullet points, ingredients, allergen warnings, and product details.
5. Clean formatting: Never output raw technical bracketed prefixes like [Product Name].
6. Conversational remarks & Gratitude: If the user sends greetings, gratitude, or casual remarks, respond warmly and naturally.
7. Keep the tone helpful, concise, professional, and grounded strictly in the provided document / supermarket food products.
"""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL") or "gemini-3.1-flash-lite"

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3),
        )
        if response.text:
            return response.text.strip()
    except Exception as e:
        logger.warning(f"LLM response synthesis failed: {e}")

    return None



def response_service(request: ResponseRequest) -> ResponseResponse:
    # Case 1: Handle greetings, clarifications, diet queries, or unsupported queries via LLM
    has_findings = bool(request.analysis and request.analysis.findings)
    analysis_findings = request.analysis.findings if has_findings else []
    ranked_evidence = rank_candidates(request.evidence, request.query, request.nutrients)
    user_diet_plan = getattr(request, "user_diet_plan", None)

    # Attempt LLM Response Synthesis first for all queries
    llm_answer = _generate_llm_response(
        query=request.query,
        evidence_list=ranked_evidence,
        findings=analysis_findings,
        triage_status=request.triage_status,
        chat_history=request.chat_history,
        user_diet_plan=user_diet_plan,
    )

    if llm_answer:
        return ResponseResponse(trace_id=request.trace_id, answer=llm_answer)

    # Fallback response for diet plan questions if LLM is unavailable
    if user_diet_plan:
        plan = user_diet_plan
        daily = plan.get("daily_targets") or {}
        q_lower = request.query.lower()
        if any(w in q_lower for w in ["diet plan", "my diet", "my plan", "calories", "macros", "target", "meals"]):
            return ResponseResponse(
                trace_id=request.trace_id,
                answer=(
                    f"Here is your active diet plan summary:\n\n"
                    f"• **Plan**: {plan.get('title', 'Personalized Blueprint')}\n"
                    f"• **Goal**: {plan.get('user_goal')}\n"
                    f"• **Daily Calorie Target**: {daily.get('daily_calories')} kcal/day\n"
                    f"• **Macronutrients**: Protein {daily.get('protein_target')}g | Carbs {daily.get('carbs_target')}g | Fat {daily.get('fat_target')}g\n"
                    f"• **Regional Market**: {plan.get('user_country', 'Global')}\n\n"
                    f"Feel free to ask me if any supermarket food product fits into this plan!"
                ),
            )

    # Fallback formatting if LLM call fails
    if request.triage_status == "UNSUPPORTED":
        q_clean = request.query.lower().strip("!.,?")
        gratitude_words = ["thanks", "thank you", "okay thanks", "ok thanks", "got it", "cool", "cheers", "bye", "awesome", "great"]
        if any(w in q_clean for w in gratitude_words):
            return ResponseResponse(
                trace_id=request.trace_id,
                answer="You're very welcome! Feel free to ask whenever you have questions about supermarket food products, ingredients, or allergens.",
            )
        return ResponseResponse(
            trace_id=request.trace_id,
            answer="Hello! I am EviBite AI, a supermarket product intelligence assistant. I specialize in packaged food products, food allergens, ingredients, and nutrition facts. How can I assist you with food products today?",
        )

    if request.triage_status == "CLARIFICATION_REQUIRED":
        return ResponseResponse(
            trace_id=request.trace_id,
            answer="Could you please specify which supermarket food product, brand, or allergen requirement you would like me to check?",
        )

    lines = []
    if analysis_findings:
        lines.append("Safety & Analysis Findings:")
        for f in analysis_findings[:5]:
            # Clean technical bracket prefixes e.g. "[Product Name] text" -> "Product Name: text"
            clean_f = f
            if clean_f.startswith("[") and "]" in clean_f:
                prod_part, rest_part = clean_f.split("]", 1)
                clean_f = f"**{prod_part[1:]}**: {rest_part.strip()}"
            lines.append(f"• {clean_f}")

    if ranked_evidence:
        lines.append("\nMatching Supermarket Products:")
        for ev in ranked_evidence[:4]:
            lines.append(f"\n**{ev.name}** (Brand: {ev.brand or 'N/A'})")
            if ev.ingredients_text:
                lines.append(f"• **Ingredients:** {ev.ingredients_text}")
            if ev.allergens:
                lines.append(f"• **Declared Allergens:** {', '.join(ev.allergens)}")
            if ev.nutrition:
                nutr_parts = [f"{k.replace('_g_100g','g').replace('_mg_100g','mg')}: {v}" for k, v in ev.nutrition.items() if v is not None]
                if nutr_parts:
                    lines.append(f"• **Nutrition (per 100g):** {', '.join(nutr_parts)}")

    answer_text = "\n".join(lines) if lines else "I checked the food product database for your query."
    return ResponseResponse(trace_id=request.trace_id, answer=answer_text)

