"""
Retrieval-Augmented Generation (RAG) Core Logic.

This module handles the orchestration of the RAG pipeline. It retrieves user
context, fetches relevant food items from the database, and streams the
response generation from the LLM.
"""

from typing import Dict, Optional, Iterator, List
from datetime import date
from sqlalchemy.orm import Session
from app.models import User, Goal, DietaryConstraint, DietHistory
from app.core.retrieval import retrieve_food_items
from app.core.generation import generate_answer
from app.core.nutrition import goal_to_targets

# Map user-facing diet names to database diet_types values
DIET_NAME_MAPPING = {
    "vegan": "Plant Based",
    "plant based": "Plant Based",
    "plant-based": "Plant Based",
    "vegetarian": "Vegetarian",
    "halal": "Halal",
    "kosher": "Kosher",
    "gluten-free": "Gluten-Free",
    "gluten free": "Gluten-Free",
}


def _normalize_diet(diet: str) -> str:
    """
    Normalize a diet preference to match database diet_types values.

    Args:
        diet (str): The raw diet string (e.g., "vegan").

    Returns:
        str: The normalized database value (e.g., "Plant Based").
    """
    return DIET_NAME_MAPPING.get(diet.lower(), diet)


def _get_user_profile(db: Session, user_id: Optional[str] = None) -> Optional[Dict]:
    """
    Fetch a user's dietary profile from the database.

    Args:
        db (Session): SQLAlchemy database session.
        user_id (Optional[str]): The Supabase user ID. If None, no lookup is performed.

    Returns:
        Optional[Dict]: A dictionary with keys "diets" (List[str]), "allergies" (List[str]),
        and "goal" (Optional[str]) when the user exists; otherwise None.
    """
    if user_id is None:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    constraints = db.query(DietaryConstraint).filter(DietaryConstraint.user_id == user_id).all()
    
    # Normalize diet names to match database values (e.g., "Vegan" -> "Plant Based")
    raw_diets = [c.constraint for c in constraints if c.constraint_type == "preference"]
    diets = [_normalize_diet(d) for d in raw_diets]
    
    allergies = [c.constraint for c in constraints if c.constraint_type == "allergy"]
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    goal = goals[0].goal if goals else None
    return {"diets": diets, "allergies": allergies, "goal": goal}


def _get_daily_status(db: Session, user_id: Optional[str], current_date: Optional[date]) -> Optional[Dict]:
    """
    Compute today's calorie/protein progress and remaining gap.
    
    Args:
        db (Session): Database session.
        user_id (str): The user ID to query.
        current_date (date): The date to calculate status for.

    Returns:
        Optional[Dict]: A dictionary containing total consumed, targets, and remaining budget.
    """
    if not user_id:
        return None

    target_date = current_date or date.today()

    goal = db.query(Goal).filter(Goal.user_id == user_id).first()
    if goal and goal.calories_target is not None and goal.protein_target is not None:
        cal_target = goal.calories_target
        protein_target = goal.protein_target
    else:
        # goal_to_targets now returns (cal, pro, carbs, fat)
        cal_target, protein_target, _, _ = goal_to_targets(goal.goal if goal else None)

    entries = (
        db.query(DietHistory)
        .filter(DietHistory.user_id == user_id)
        .filter(DietHistory.date == target_date)
        .all()
    )

    calories_total = sum(e.calories or 0 for e in entries)
    protein_total = sum(e.protein_g or 0 for e in entries)

    return {
        "calories_total": calories_total,
        "calories_target": cal_target,
        "protein_total": protein_total,
        "protein_target": protein_target,
        "remaining_calories": max(cal_target - calories_total, 0),
        "remaining_protein": max(protein_target - protein_total, 0),
    }


def rag_answer_stream(
    query: str,
    db: Session,
    user_id: Optional[str] = None,
    history_text: Optional[str] = None,
    manual_filters: Optional[Dict] = None,
    current_date: Optional[date] = None,
) -> Iterator[str]:
    """
    Run the RAG pipeline and stream the generated answer as chunks.

    The function retrieves relevant menu items for the current day based on the
    user's natural language question and optional profile, then streams an LLM
    answer in text chunks suitable for HTTP streaming responses.

    Args:
        query (str): The user's natural language question.
        db (Session): SQLAlchemy database session.
        user_id (Optional[str]): Optional Supabase user ID to enrich retrieval with
            user-specific diets, allergies, and goals.
        history_text (Optional[str]): Optional conversation history for context.
        manual_filters (Optional[Dict]): Manual UI-selected filters that take priority
            over AI-parsed filters. Keys: 'dining_halls' (List[str]), 'meals' (List[str]).
        current_date (Optional[date]): Date to filter by. If None, uses today's date.

    Returns:
        Iterator[str]: A generator that yields segments of the assistant's response.
    """
    user_profile = _get_user_profile(db, user_id)
    daily_status = _get_daily_status(db, user_id, current_date)
    food_items = retrieve_food_items(
        query,
        db,
        user_profile,
        limit=10,
        manual_filters=manual_filters,
        current_date=current_date,
    )
    return generate_answer(query, food_items, user_profile, history_text, daily_status=daily_status)