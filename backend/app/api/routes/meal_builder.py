"""
Meal Builder API.

This module provides logic for automatically generating meal plans
that fit a user's nutritional goals and dietary restrictions.
"""

from datetime import date
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.nutrition import goal_to_targets
from app.core.rag import _get_user_profile
from app.core.retrieval import retrieve_food_items
from app.models import DietHistory, Goal, User

# Demo mode date constant
DEMO_DATE = date(2025, 12, 12)

router = APIRouter()

class MealBuilderRequest(BaseModel):
    """
    Request payload for meal plan suggestion.

    Attributes:
        user_id (str): User requesting the plan.
        date (Any): Date for the meal plan (parses to date object).
        calorie_target (float): Specific calorie target override.
        protein_target (float): Specific protein target override.
        dining_halls (List[str]): Filter by dining halls.
        meals (List[str]): Filter by meals.
        max_items (int): Max items to suggest per plan.
        demo_mode (bool): If True, use Dec 12 2025 menu data.
    """
    user_id: str
    date: Optional[Any] = None  # Allow Any to bypass initial strict typing, validated by parser
    calorie_target: Optional[float] = None
    protein_target: Optional[float] = None
    dining_halls: Optional[List[str]] = None
    meals: Optional[List[str]] = None
    max_items: int = 4
    demo_mode: Optional[bool] = False  # Demo mode: use historical menu data

    @model_validator(mode='before')
    @classmethod
    def parse_date(cls, data: Any) -> Any:
        if isinstance(data, dict) and 'date' in data:
            if isinstance(data['date'], str):
                try:
                    # Handle YYYY-MM-DD
                    data['date'] = date.fromisoformat(data['date'])
                except ValueError:
                    # If empty string or invalid, default to None (which becomes today)
                    data['date'] = None
        return data


def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _compute_daily_gap(db: Session, user_id: str, target_date: date) -> Dict[str, float]:
    """Calculate nutrition remaining for the day."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    goal = db.query(Goal).filter(Goal.user_id == user_id).first()
    
    # Defaults
    cal_target, protein_target, carbs_target, fat_target = goal_to_targets(goal.goal if goal else None)

    if goal:
        if goal.calories_target is not None:
            cal_target = goal.calories_target
        if goal.protein_target is not None:
            protein_target = goal.protein_target

    entries = (
        db.query(DietHistory)
        .filter(DietHistory.user_id == user_id)
        .filter(DietHistory.date == target_date)
        .all()
    )

    calories_total = sum(e.calories or 0 for e in entries)
    protein_total = sum(e.protein_g or 0 for e in entries)
    # Placeholder: currently DB doesn't track historical carbs/fat
    carbs_total = 0 
    fat_total = 0

    return {
        "calories_total": calories_total,
        "calories_target": cal_target,
        "protein_total": protein_total,
        "protein_target": protein_target,
        "carbs_total": carbs_total,
        "carbs_target": carbs_target,
        "fat_total": fat_total,
        "fat_target": fat_target,
        "remaining_calories": max(cal_target - calories_total, 0),
        "remaining_protein": max(protein_target - protein_total, 0),
        "remaining_carbs": max(carbs_target - carbs_total, 0),
        "remaining_fat": max(fat_target - fat_total, 0),
    }


def _simplify_items(items: List) -> List[Dict]:
    """Convert DB objects to simple dictionaries for the meal builder."""
    simplified = []
    for item in items:
        calories = float(item.calories) if item.calories is not None else 0.0
        protein = float(item.protein_g) if item.protein_g is not None else 0.0
        carbs = float(item.carbs_g) if item.carbs_g is not None else 0.0
        fat = float(item.fat_g) if item.fat_g is not None else 0.0
        
        simplified.append(
            {
                "id": item.id,
                "item": item.item,
                "dining_hall": item.dining_hall,
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fat": fat,
                "availability": item.availability_today or [],
                "diet_types": item.diet_types or [],
            }
        )
    return simplified


def _build_plan(
    items: List[Dict],
    calorie_target: float,
    protein_target: float,
    max_items: int,
    mode: str,
) -> Dict:
    """Construct a specific meal plan strategy (e.g. high protein)."""
    if not items:
        return {"label": "No items available", "items": [], "totals": {"calories": 0, "protein": 0}}

    # Scoring logic based on mode
    if mode == "protein":
        # Prioritize protein density (protein per calorie)
        ranked = sorted(
            items,
            key=lambda x: (
                -(x["protein"] / x["calories"]) if x["calories"] > 10 else 0,
                -x["protein"],
            ),
        )
        label = "High Protein Focus"
    elif mode == "low_carb":
        # Prioritize low carb + high protein
        ranked = sorted(
            items,
            key=lambda x: (
                x.get("carbs", 999),  # Ascending carbs
                -x["protein"],        # Descending protein
            ),
        )
        label = "Low Carb / Keto Friendly"
    elif mode == "convenience":
        # Group by dining hall first
        # We pick the most frequent dining hall in the top 10 items
        if not items:
            return {"label": "Convenience (Same Hall)", "items": [], "totals": {}}
        
        # Simple heuristic: sort by protein first to find "good" items, then stick to one hall
        base_ranked = sorted(items, key=lambda x: -x["protein"])
        
        # Find best hall from top 5 items
        top_halls = [x["dining_hall"] for x in base_ranked[:5]]
        if top_halls:
            best_hall = max(set(top_halls), key=top_halls.count)
            # Filter items to only this hall
            ranked = [x for x in base_ranked if x["dining_hall"] == best_hall]
            label = f"Convenience ({best_hall})"
        else:
            ranked = base_ranked
            label = "Convenience"
    elif mode == "volume":
        # Prioritize low calorie density (filling foods)
        # Sort by calories ascending, protein descending
        ranked = sorted(
            items,
            key=lambda x: (
                x["calories"], 
                -x["protein"]
            ),
        )
        label = "Volume / Light Meal"
    else: # mode == "balanced"
        # Try to hit calorie target closest
        ranked = sorted(
            items,
            key=lambda x: (
                abs(x["calories"] - (calorie_target / max_items)), # Item that is roughly 1/Nth of target
                -x["protein"],
            ),
        )
        label = "Balanced Plate"

    selected: List[Dict] = []
    seen_names = set()
    total_cal = 0.0
    total_pro = 0.0
    total_carbs = 0.0
    total_fat = 0.0

    for food in ranked:
        if len(selected) >= max_items:
            break
            
        # Deduplication: check if item name is already in selected (fuzzy match or exact)
        if food["item"] in seen_names:
            continue
            
        selected.append(food)
        seen_names.add(food["item"])
        
        total_cal += food["calories"]
        total_pro += food["protein"]
        total_carbs += food.get("carbs", 0)
        total_fat += food.get("fat", 0)

        # Stop if we hit targets (with some buffer)
        if total_pro >= protein_target and total_cal >= calorie_target * 0.95:
            break

    return {
        "label": label,
        "items": selected,
        "totals": {
            "calories": round(total_cal, 1), 
            "protein": round(total_pro, 1),
            "carbs": round(total_carbs, 1),
            "fat": round(total_fat, 1)
        },
    }


@router.post("/suggest")
def suggest_meal_plan(req: MealBuilderRequest, db: Session = Depends(get_db)):
    """
    Generate multiple meal plan options based on user goals.

    Calculates the user's remaining nutritional budget for the day and
    builds 4 distinct plans:
    1. High Protein
    2. Balanced
    3. Low Carb
    4. Convenience (or Volume)

    Args:
        req (MealBuilderRequest): Request parameters.
        db (Session): Database session.

    Returns:
        dict: The generated plans and remaining budget info.
    """
    # req.date will be a date object or None after validation, OR a string if validation failed to convert it but kept it as string.
    # We ensure it's a date object here.
    target_date = req.date if isinstance(req.date, date) else date.today()
    if isinstance(req.date, str):
        try:
            target_date = date.fromisoformat(req.date)
        except ValueError:
            target_date = date.today()

    # Determine menu date for "split reality" demo mode
    # User's daily gap is calculated from target_date (their log date)
    # Menu items are retrieved from demo date if demo_mode is enabled
    menu_date = DEMO_DATE if req.demo_mode else target_date

    gap = _compute_daily_gap(db, req.user_id, target_date)

    target_calories = req.calorie_target if req.calorie_target is not None else gap["remaining_calories"]
    target_protein = req.protein_target if req.protein_target is not None else gap["remaining_protein"]

    # Ensure non-negative targets
    target_calories = max(target_calories, 0)
    target_protein = max(target_protein, 0)
    
    # We will just pass remaining carbs/fat for display purposes mostly
    # But if we were to optimize for them, we'd need them in the logic
    remaining_carbs = gap["remaining_carbs"]
    remaining_fat = gap["remaining_fat"]

    manual_filters: Dict[str, List[str]] = {}
    
    # Strictly filter by selected dining hall if provided
    # The frontend sends a list in `dining_halls` if specific hall selected
    if req.dining_halls:
        # We only take the first one if user selected a single hall for cohesion
        manual_filters["dining_halls"] = req.dining_halls
        
    if req.meals:
        manual_filters["meals"] = req.meals

    user_profile = _get_user_profile(db, req.user_id)

    # Use menu_date for item retrieval (demo reality)
    items = retrieve_food_items(
        query="high protein options",
        db=db,
        user_profile=user_profile,
        limit=25,
        manual_filters=manual_filters or None,
        current_date=menu_date,
    )

    simplified = [item for item in _simplify_items(items) if item["calories"] or item["protein"]]

    if not simplified:
        return {
            "status": "no-items",
            "message": "No menu items available for the selected date/filters.",
            "remaining": {
                "calories": gap["remaining_calories"], 
                "protein": gap["remaining_protein"],
                "carbs": gap["remaining_carbs"],
                "fat": gap["remaining_fat"]
            },
            "meals": [],
        }

    max_items = max(1, min(req.max_items, 6))
    
    # Generate 4 distinct plans
    protein_plan = _build_plan(simplified, target_calories, target_protein, max_items, mode="protein")
    balanced_plan = _build_plan(simplified, target_calories, target_protein, max_items, mode="balanced")
    low_carb_plan = _build_plan(simplified, target_calories, target_protein, max_items, mode="low_carb")
    
    # If user selected a specific dining hall, "Convenience" is redundant (all are convenient).
    # We can replace it with "Volume" (low calorie density) or just omit/rename it.
    # For now, let's keep it but rename it to "Chef's Choice" for variety if hall is selected.
    is_single_hall = req.dining_halls and len(req.dining_halls) == 1
    
    convenience_mode = "volume" if is_single_hall else "convenience"
    fourth_plan = _build_plan(simplified, target_calories, target_protein, max_items, mode=convenience_mode)

    return {
        "status": "success",
        "remaining": {
            "calories": gap["remaining_calories"], 
            "protein": gap["remaining_protein"],
            "carbs": gap["remaining_carbs"],
            "fat": gap["remaining_fat"]
        },
        "meals": [protein_plan, balanced_plan, low_carb_plan, fourth_plan],
    }