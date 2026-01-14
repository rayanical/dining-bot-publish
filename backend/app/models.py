"""
Database Models.

This module defines the SQLAlchemy ORM models representing the database schema.
It includes definitions for Users, Goals, Dietary Constraints, and Menu Items.
"""

from sqlalchemy import Column, Integer, String, Float, ARRAY, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
from sqlalchemy.sql import func

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None

class User(Base):
    """
    Represents a registered user in the system.

    Attributes:
        id (str): Unique identifier (primary key).
        email (str): User's email address.
        goals (List[Goal]): One-to-many relationship with user goals.
        dietary_constraints (List[DietaryConstraint]): One-to-many relationship with dietary constraints.
        diet_history (List[DietHistory]): One-to-many relationship with food logs.
        personal_menus (List[PersonalMenu]): One-to-many relationship with saved personal menus.
    """
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    
    goals = relationship("Goal", back_populates="user")
    dietary_constraints = relationship("DietaryConstraint", back_populates="user")
    diet_history = relationship("DietHistory", back_populates="user")
    personal_menus = relationship("PersonalMenu", back_populates="user")

class Goal(Base):
    """
    Represents a user's health or nutrition goal.

    Attributes:
        id (int): Primary key.
        user_id (str): Foreign key to the User table.
        goal (str): Text description of the goal (e.g., "Build Muscle").
        success_metric (str): Optional metric to measure success.
        progress (str): Optional text tracking progress.
        calories_target (int): Daily calorie target.
        protein_target (int): Daily protein target in grams.
        user (User): Relationship to the parent User.
    """
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    goal = Column(String, nullable=False)
    success_metric = Column(String, nullable=True)
    progress = Column(String, nullable=True)
    calories_target = Column(Integer, nullable=True)
    protein_target = Column(Integer, nullable=True)
    user = relationship("User", back_populates="goals")

class DietaryConstraint(Base):
    """
    Represents a specific dietary restriction or preference (e.g., "Vegan", "Peanut Allergy").

    Attributes:
        id (int): Primary key.
        user_id (str): Foreign key to the User table.
        constraint (str): Name of the constraint.
        constraint_type (str): Type of constraint (e.g., "allergy", "preference").
        user (User): Relationship to the parent User.
    """
    __tablename__ = "dietary_constraints"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    constraint = Column(String, nullable=False)
    constraint_type = Column(String, nullable=False)
    user = relationship("User", back_populates="dietary_constraints")

class DietHistory(Base):
    """
    Represents a log of food consumed by the user.

    Attributes:
        id (int): Primary key.
        user_id (str): Foreign key to the User table.
        date (Date): The date the food was consumed.
        item (str): Name of the food item.
        mealtime (str): Time of day/meal type (e.g., "Lunch").
        calories (float): Calories consumed.
        protein_g (float): Protein consumed in grams.
        allergens (List[str]): List of allergens in the food.
        diet_types (List[str]): List of diet types the food satisfies.
        user (User): Relationship to the parent User.
    """
    __tablename__ = "diet_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    item = Column(String, nullable=False)
    mealtime = Column(String, nullable=False)
    calories = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=True)
    allergens = Column(ARRAY(String), nullable=False)
    diet_types = Column(ARRAY(String), nullable=False)
    user = relationship("User", back_populates="diet_history")

class PersonalMenu(Base):
    """
    Represents a custom menu item saved by the user.

    Attributes:
        id (int): Primary key.
        user_id (str): Foreign key to the User table.
        item (str): Name of the menu item.
        calories (float): Caloric content.
        allergens (List[str]): List of allergens.
        diet_types (List[str]): List of diet types.
        user (User): Relationship to the parent User.
    """
    __tablename__ = "personal_menu"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    item = Column(String, nullable=False)
    calories = Column(Float, nullable=True)
    allergens = Column(ARRAY(String), nullable=True)
    diet_types = Column(ARRAY(String), nullable=True)
    user = relationship("User", back_populates="personal_menus")

class DiningHallMenu(Base):
    """
    Represents a food item available at a dining hall.

    This table stores scraped menu data, including nutritional info and embeddings
    for semantic search.

    Attributes:
        id (int): Primary key.
        item (str): Name of the dish.
        dining_hall (str): Name of the dining hall.
        last_updated (Date): Date when this record was last updated/scraped.
        calories (float): Caloric content.
        serving_size (str): Serving size description.
        fat_g (float): Total fat in grams.
        sat_fat_g (float): Saturated fat in grams.
        trans_fat_g (float): Trans fat in grams.
        cholesterol_mg (float): Cholesterol in mg.
        sodium_mg (float): Sodium in mg.
        carbs_g (float): Total carbohydrates in grams.
        fiber_g (float): Dietary fiber in grams.
        sugars_g (float): Sugars in grams.
        protein_g (float): Protein in grams.
        allergens (List[str]): List of allergens.
        diet_types (List[str]): List of applicable diets (e.g., Vegan, Gluten-Free).
        availability_today (List[str]): List of meal times available today (e.g., ["Lunch", "Dinner"]).
        ingredients (List[str]): List of ingredients.
        embedding (Vector): Vector embedding for semantic search (if pgvector is enabled).
    """
    __tablename__ = "dining_hall_menu"
    
    id = Column(Integer, primary_key=True, index=True)
    item = Column(String, nullable=False, index=True)
    dining_hall = Column(String, nullable=False, index=True)
    
    last_updated = Column(Date, default=func.now(), nullable=False)

    # Nutritional Info
    calories = Column(Float, nullable=True)
    serving_size = Column(String, nullable=True)
    fat_g = Column(Float, nullable=True)
    sat_fat_g = Column(Float, nullable=True)
    trans_fat_g = Column(Float, nullable=True)
    cholesterol_mg = Column(Float, nullable=True)
    sodium_mg = Column(Float, nullable=True)
    carbs_g = Column(Float, nullable=True)
    fiber_g = Column(Float, nullable=True)
    sugars_g = Column(Float, nullable=True)
    protein_g = Column(Float, nullable=True)
    
    allergens = Column(ARRAY(String), nullable=True)
    diet_types = Column(ARRAY(String), nullable=True)
    availability_today = Column(ARRAY(String), nullable=True)
    
    ingredients = Column(ARRAY(String), nullable=True)
    
    embedding = Column(Vector(1536), nullable=True) if PGVECTOR_AVAILABLE else None

    __table_args__ = (
        UniqueConstraint('item', 'dining_hall', name='uix_item_dining_hall'),
    )