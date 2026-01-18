"""
Food Search API.

This module provides endpoints for searching the dining hall menu database
using structured filters (hall, meal, diet, etc.) or text search.
"""

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import SessionLocal
from app.models import DiningHallMenu
from app.core.retrieval import retrieve_food_items
from app.schemas import FoodItem

# Demo mode date constant
DEMO_DATE = date(2025, 12, 12)

router = APIRouter()

def get_db():
    """Dependency to provide a database session."""
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("/search", response_model=List[FoodItem])
def search_food(
    q: Optional[str] = Query(None, description="Search term"),
    dining_hall: Optional[str] = Query(None),
    meal: Optional[str] = Query(None),
    diets: Optional[List[str]] = Query(None),
    allergies: Optional[List[str]] = Query(None),
    min_calories: Optional[float] = Query(None),
    max_calories: Optional[float] = Query(None),
    limit: int = Query(50),
    demo_mode: bool = Query(False, description="Use Dec 12 2025 demo menu data"),
    db: Session = Depends(get_db)
):
    """
    Search for food items with various filters.

    Args:
        q (str): Text search query for item name.
        dining_hall (str): Filter by dining hall name.
        meal (str): Filter by meal (e.g., "Lunch").
        diets (List[str]): List of diets the item must satisfy.
        allergies (List[str]): List of allergens to exclude.
        min_calories (float): Minimum calorie count.
        max_calories (float): Maximum calorie count.
        limit (int): Max results to return.
        demo_mode (bool): If True, use Dec 12 2025 menu data.
        db (Session): Database session.

    Returns:
        List[FoodItem]: List of matching food items.
    """
    hall_filter = dining_hall.capitalize() if dining_hall else None
    
    structured_filters = {
        "item_name": q,  # Pass text query as item_name filter
        "dining_hall": hall_filter,
        "meal": meal,
        "diets": diets or [],
        "allergies": allergies or [],
        "min_calories": min_calories,
        "max_calories": max_calories,
    }

    # Use demo date if demo mode is enabled
    target_date = DEMO_DATE if demo_mode else None

    # Pass empty query string so we rely purely on structured_filters
    items = retrieve_food_items(
        query="", 
        db=db,
        limit=limit,
        structured_filters=structured_filters,
        current_date=target_date,
    )
    return items

@router.get("/options")
def get_filter_options(db: Session = Depends(get_db)):
    """
    Get available filter options for the UI.

    Returns:
        dict: Lists of available dining halls, meals, and supported diets.
    """
    halls_query = db.query(DiningHallMenu.dining_hall).distinct().all()
    dining_halls = sorted([h[0] for h in halls_query if h[0]])
    return {
        "dining_halls": dining_halls,
        "meals": ["Breakfast", "Lunch", "Dinner", "Late Night", "Brunch", "Grab' n Go"],
        "diets": ["Vegan", "Vegetarian", "Halal", "Kosher", "Gluten-Free", "Sustainable"]
    }