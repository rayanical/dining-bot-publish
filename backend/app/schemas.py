"""
Pydantic Schemas.

This module defines Pydantic models for data validation, serialization,
and type hinting across API requests and responses.
"""

from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date

class UserProfileCreate(BaseModel):
    """
    Schema for creating or updating a user profile.
    """
    user_id: str
    email: str
    diets: List[str]
    allergies: List[str]
    goal: str
    dislikes: Optional[str] = None
    liked_cuisines: List[str]

class FoodItem(BaseModel):
    """
    Schema representing a detailed food item returned to the client.
    """
    id: int
    item: str
    dining_hall: str
    calories: Optional[float] = None
    serving_size: Optional[str] = None
    fat_g: Optional[float] = None
    sat_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    cholesterol_mg: Optional[float] = None
    sodium_mg: Optional[float] = None
    carbs_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugars_g: Optional[float] = None
    protein_g: Optional[float] = None
    
    allergens: Optional[List[str]] = None
    diet_types: Optional[List[str]] = None
    availability_today: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)

class FoodLogCreate(BaseModel):
    """
    Schema for logging a food item eaten by the user.
    """
    item_name: str 
    meal_type: str 
    calories: float
    protein: Optional[float] = 0.0
    date: Optional[str] = None # Accepts "2024-03-20" string from frontend

class CustomGoalUpdate(BaseModel):
    """
    Schema for updating specific nutritional targets.
    """
    calories: int
    protein: int