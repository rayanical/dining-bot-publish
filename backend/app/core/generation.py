"""
LLM Generation Module.

This module handles formatting data for the LLM and managing the OpenAI API
interaction for generating natural language responses.
"""

from typing import List, Dict, Optional, Iterator
from openai import OpenAI
from app.models import DiningHallMenu
from app.core.config import OPENAI_API_KEY

_client = OpenAI(api_key=OPENAI_API_KEY)

def format_food_item(item: DiningHallMenu) -> str:
    """
    Format a menu row into a human-readable string for prompting.

    Args:
        item (DiningHallMenu): A row representing a dining hall menu item.

    Returns:
        str: A multi-line string with key fields (hall, availability, calories,
        allergens, diet types) suitable as LLM context.
    """
    availability = ', '.join(item.availability_today) if item.availability_today else 'Unknown'
    allergens_str = ', '.join(item.allergens) if item.allergens else 'None'
    diet_types_str = ', '.join(item.diet_types) if item.diet_types else 'None'
    ingredients_str = ', '.join(item.ingredients) if item.ingredients else 'Not listed'
    
    # Nutritional info
    calories_str = f"{item.calories:.1f}" if item.calories is not None else "N/A"
    protein_str = f"{item.protein_g:.1f}g" if item.protein_g is not None else "N/A"
    carbs_str = f"{item.carbs_g:.1f}g" if item.carbs_g is not None else "N/A"
    fat_str = f"{item.fat_g:.1f}g" if item.fat_g is not None else "N/A"
    sugar_str = f"{item.sugars_g:.1f}g" if item.sugars_g is not None else "N/A"
    
    return f"""Item: {item.item}
Dining Hall: {item.dining_hall}
Available Today: {availability}
Calories: {calories_str}
Protein: {protein_str}
Carbs: {carbs_str}
Fat: {fat_str}
Sugar: {sugar_str}
Allergens: {allergens_str}
Diet Types: {diet_types_str}
Ingredients: {ingredients_str}"""

def generate_answer(
    query: str,
    food_items: List[DiningHallMenu],
    user_profile: Optional[Dict] = None,
    history_text: Optional[str] = None,
    daily_status: Optional[Dict] = None,
) -> Iterator[str]:
    """
    Generate a streaming answer from the LLM using retrieved items.

    This yields text chunks suitable for FastAPI StreamingResponse and the
    Vercel AI SDK proxy, enabling token-by-token rendering on the client.

    Args:
        query (str): The user's question.
        food_items (List[DiningHallMenu]): Menu items retrieved by the retriever.
        user_profile (Optional[Dict]): Optional dict containing "diets",
            "allergies", and "goal" to inform the response tone/content.
        history_text (Optional[str]): Optional conversation history.
        daily_status (Optional[Dict]): Optional status of user's daily nutrition targets.

    Returns:
        Iterator[str]: A generator yielding incremental segments of the model's
        response. If an error occurs, an explanatory message is yielded.
    """
    if not food_items:
        yield "I couldn't find any menu items matching your request for today. This could mean:\n\n1. **No matching items available** - Try broadening your search or removing some filters.\n2. **Menus not yet updated** - Today's menus may not have been scraped yet. Please check back later.\n\nIf you believe this is an error, try refreshing the page or checking back in a few minutes."
        return
    
    context_items = "\n\n---\n\n".join([format_food_item(item) for item in food_items])
    
    system_prompt = """You are Dining Bot, a helpful assistant for UMass Dining. 
Answer the user's question using ONLY the provided menu data below. 
Do not make up or invent any food items. 
If the answer isn't in the provided data, say so clearly.
Be concise, friendly, and include specific details like dining hall, station, and nutritional information when relevant.
NEVER guess allergen information - only use what is explicitly provided in the menu data."""
    
    user_context = f"""User Question: {query}

Menu Data (retrieved from today's dining halls):
{context_items}

Instructions:
- Answer the question using ONLY the menu data provided above
- Include specific details like dining hall name, station, and nutritional values
- If the user asks for "best" options, prioritize items with higher protein or better nutritional profiles
- Be concise and helpful
- If the user has dietary constraints mentioned in their question, make sure to respect those
- NEVER infer or guess allergen data - only repeat exactly what is provided"""
    
    if daily_status:
        daily_context = (
            "[Current Daily Status]\n"
            f"- Eaten: {daily_status['calories_total']} kcal (Goal: {daily_status['calories_target']})\n"
            f"- Protein: {daily_status['protein_total']}g (Goal: {daily_status['protein_target']}g)\n"
            f"- REMAINING BUDGET: {daily_status['remaining_calories']} kcal, {daily_status['remaining_protein']}g protein\n\n"
        )
        user_context = daily_context + user_context

    if user_profile:
        profile_context = "\nUser Profile:\n"
        if user_profile.get("diets"):
            profile_context += f"- Dietary restrictions: {', '.join(user_profile['diets'])}\n"
        if user_profile.get("allergies"):
            profile_context += f"- Allergies: {', '.join(user_profile['allergies'])}\n"
        if user_profile.get("goal"):
            profile_context += f"- Health goal: {user_profile['goal']}\n"
        user_context = profile_context + "\n" + user_context

    if history_text:
        user_context = (
            "Conversation so far (for context, do not repeat verbatim):\n"
            + history_text
            + "\n\n"
            + user_context
        )
    
    try:
        stream = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_context}
            ],
            temperature=0.2,
            max_tokens=500,
            stream=True,
        )

        for chunk in stream:
            try:
                delta = chunk.choices[0].delta
                if delta and getattr(delta, "content", None):
                    yield delta.content
            except Exception:
                # Be resilient to partial chunks
                continue
    except Exception as e:
        yield f"I encountered an error generating a response: {str(e)}"