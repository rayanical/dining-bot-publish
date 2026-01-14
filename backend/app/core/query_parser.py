from __future__ import annotations

import re
import logging
from typing import Dict, List, Optional, Literal

from openai import OpenAI
from pydantic import BaseModel, Field

from app.core.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)


class SearchFilters(BaseModel):
    dining_halls: Optional[List[str]] = None
    meals: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    allergens_to_exclude: Optional[List[str]] = None
    nutritional_constraints: Optional[Dict[str, float]] = None
    sort_by: Optional[str] = None


class SearchIntent(BaseModel):
    intent_type: Literal["factual_lookup", "semantic_search", "hybrid"]
    search_query: str
    filters: SearchFilters
    reasoning: str


def _legacy_parse_user_query(query: str, user_profile: Optional[Dict] = None) -> Dict:
    """Legacy regex parser kept as a fallback."""
    query_lower = query.lower()
    filters: Dict = {
        "dining_hall": None,
        "meal": None,
        "diets": [],
        "allergies": [],
        "min_protein": None,
        "max_protein": None,
        "min_calories": None,
        "max_calories": None,
        "keywords": [],
    }

    dining_halls = ["berkshire", "worcester", "franklin", "hampshire"]
    for hall in dining_halls:
        if hall in query_lower:
            filters["dining_hall"] = hall.capitalize()
            break

    meals = ["breakfast", "lunch", "dinner", "late night", "brunch", "grab' n go"]
    for meal in meals:
        if meal in query_lower:
            filters["meal"] = meal.lower()
            break

    diet_keywords = {
        "vegan": "Plant Based",
        "plant based": "Plant Based",
        "plant-based": "Plant Based",
        "vegetarian": "Vegetarian",
        "halal": "Halal",
        "kosher": "Kosher",
        "gluten-free": "Gluten-Free",
        "gluten free": "Gluten-Free",
    }
    for keyword, diet in diet_keywords.items():
        if keyword in query_lower:
            filters["diets"].append(diet)

    protein_patterns = [
        (r"high\s+protein", ("min_protein", 20)),
        (r"protein\s+rich", ("min_protein", 20)),
        (r"best\s+protein", ("min_protein", 15)),
        (r"(\d+)\s*g\s*protein", ("min_protein", None)),
    ]
    for pattern, (key, default) in protein_patterns:
        match = re.search(pattern, query_lower)
        if match:
            if default is None and match.groups():
                filters[key] = float(match.group(1))
            elif default is not None:
                filters[key] = default
            break

    calorie_patterns = [
        (r"low\s+calorie", ("max_calories", 400)),
        (r"(\d+)\s+calories?", ("max_calories", None)),
    ]
    for pattern, (key, default) in calorie_patterns:
        match = re.search(pattern, query_lower)
        if match:
            if default is None and match.groups():
                filters[key] = float(match.group(1))
            elif default is not None:
                filters[key] = default
            break

    important_words = ["best", "top", "recommend", "find", "where", "what"]
    for word in important_words:
        if word in query_lower:
            filters["keywords"].append(word)

    if user_profile:
        if user_profile.get("diets"):
            filters["diets"].extend(user_profile["diets"])
            filters["diets"] = list(set(filters["diets"]))

        if user_profile.get("allergies"):
            filters["allergies"] = user_profile["allergies"]

        if user_profile.get("goal") == "Gain Muscle / Weight":
            if filters["min_protein"] is None:
                filters["min_protein"] = 20
        elif user_profile.get("goal") == "Lose Weight":
            if filters["max_calories"] is None:
                filters["max_calories"] = 500

    return filters


_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are a semantic router for dining-hall food search. Output a structured intent with filters.
Map vague language to concrete constraints and keep results broad so multiple portions remain viable.

Portion Scaling Logic (CRUCIAL):
- If user asks for high protein or specific grams (e.g., 25g, 30g, 40g), DO NOT set a high min_protein.
- Instead, set min_protein to a unit floor of 8-10 grams to avoid filtering out moderate items.
- Also set sort_by="protein_desc" when protein targeting is implied.
- Calories: if user says "under/less than X calories", set max_calories to X.

Intent guidance:
- factual_lookup: precise, location/mealtime/diet stated ("chicken at Worcester dinner").
- semantic_search: vibe/feelings ("comfort food", "something spicy").
- hybrid: mixed vibe + constraints ("spicy food at Worcester", "40g protein dinner").

Filters guidance:
- dining_halls: capitalize known halls.
- dietary_restrictions: include diets from user profile or query (Vegan, Halal, Kosher, Gluten-Free, Vegetarian, Plant Based).
- allergens_to_exclude: explicit allergy mentions.
- nutritional_constraints: use keys like min_protein, max_protein, min_calories, max_calories.
- meals: include meal words (breakfast/lunch/dinner/late night/brunch).

Reasoning: briefly explain why filters were chosen (e.g., "User said gym -> high protein, so set min_protein 10 and sort by protein desc").
"""


def _apply_portion_scaling(intent: SearchIntent) -> SearchIntent:
    """Apply portion scaling logic to prevent overly restrictive protein filters."""
    # Null-safety: ensure filters object exists
    if intent.filters is None:
        intent.filters = SearchFilters()
    
    nc = intent.filters.nutritional_constraints or {}
    min_protein = nc.get("min_protein")
    if min_protein is not None:
        if min_protein >= 15:
            nc["min_protein"] = 10
        elif min_protein < 8:
            nc["min_protein"] = 8
        if intent.filters.sort_by is None:
            intent.filters.sort_by = "protein_desc"
    
    # Set to None if empty to match Optional schema
    intent.filters.nutritional_constraints = nc if nc else None
    return intent


def ai_parse_query(query: str, user_profile: Optional[Dict] = None) -> SearchIntent:
    """LLM-based semantic router with structured output and portion scaling."""
    user_context_lines = []
    if user_profile:
        diets = user_profile.get("diets") or []
        allergies = user_profile.get("allergies") or []
        goal = user_profile.get("goal")
        if diets:
            user_context_lines.append(f"User diets: {', '.join(diets)}")
        if allergies:
            user_context_lines.append(f"Allergies to exclude: {', '.join(allergies)}")
        if goal:
            user_context_lines.append(f"Goal: {goal}")
    context_block = "\n".join(user_context_lines) if user_context_lines else "(no profile provided)"

    try:
        response = _client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Query: {query}\nProfile: {context_block}"},
            ],
            response_format=SearchIntent,
            temperature=0,
        )
        intent: SearchIntent = response.choices[0].message.parsed  # type: ignore
        intent = _apply_portion_scaling(intent)
        logger.info(f"Successfully parsed query with LLM: intent={intent.intent_type}")
        return intent
    except Exception as e:
        logger.warning(f"LLM query parsing failed, falling back to legacy parser: {e}")
        legacy_filters = _legacy_parse_user_query(query, user_profile)
        
        # Convert legacy filters to new schema (using None for empty lists)
        dining_hall = legacy_filters.get("dining_hall")
        meal = legacy_filters.get("meal")
        diets = legacy_filters.get("diets") or []
        allergies = legacy_filters.get("allergies") or []
        
        nutritional_constraints = {
            k: v
            for k, v in {
                "min_protein": legacy_filters.get("min_protein"),
                "max_protein": legacy_filters.get("max_protein"),
                "min_calories": legacy_filters.get("min_calories"),
                "max_calories": legacy_filters.get("max_calories"),
            }.items()
            if v is not None
        }
        
        fallback_filters = SearchFilters(
            dining_halls=[dining_hall] if dining_hall else None,
            meals=[meal] if meal else None,
            dietary_restrictions=diets if diets else None,
            allergens_to_exclude=allergies if allergies else None,
            nutritional_constraints=nutritional_constraints if nutritional_constraints else None,
            sort_by=None,
        )
        return SearchIntent(
            intent_type="hybrid",
            search_query=query,
            filters=fallback_filters,
            reasoning="Fallback to legacy regex parser due to LLM error.",
        )


__all__ = ["SearchIntent", "SearchFilters", "ai_parse_query"]

