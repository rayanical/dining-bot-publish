"""
Database Initialization.

This module contains logic to seed the database with initial menu data
by running the scraper and mapping the results to the database schema.
"""

from app.core.database import engine, Base, SessionLocal
from app.models import DiningHallMenu
from app.core.scraper import scrape_all_menus
from datetime import datetime
from collections import defaultdict
import sqlalchemy.exc

def map_scraper_data_to_schema(scraped_items):
    """
    Map scraper items to dining_hall_menu schema, grouping meals per item/hall.
    
    Args:
        scraped_items (List[dict]): Raw data from the scraper.

    Returns:
        List[dict]: Processed data ready for insertion into the database.
    """
    grouped = defaultdict(lambda: {
        "item": None,
        "dining_hall": None,
        "calories": None,
        "serving_size": None,
        "fat_g": None,
        "sat_fat_g": None,
        "trans_fat_g": None,
        "cholesterol_mg": None,
        "sodium_mg": None,
        "carbs_g": None,
        "fiber_g": None,
        "sugars_g": None,
        "protein_g": None,
        "allergens": set(),
        "diet_types": set(),
        "availability_today": set(),
        "ingredients": set(),  # Use set to deduplicate ingredients across meals
    })
    
    for item in scraped_items:
        key = (item["name"], item["dining_hall"])
        
        if grouped[key]["item"] is None:
            grouped[key]["item"] = item["name"]
            grouped[key]["dining_hall"] = item["dining_hall"]
            grouped[key]["calories"] = item.get("calories")
            grouped[key]["serving_size"] = item.get("serving_size")
            grouped[key]["fat_g"] = item.get("fat_g")
            grouped[key]["sat_fat_g"] = item.get("sat_fat_g")
            grouped[key]["trans_fat_g"] = item.get("trans_fat_g")
            grouped[key]["cholesterol_mg"] = item.get("cholesterol_mg")
            grouped[key]["sodium_mg"] = item.get("sodium_mg")
            grouped[key]["carbs_g"] = item.get("carbs_g")
            grouped[key]["fiber_g"] = item.get("fiber_g")
            grouped[key]["sugars_g"] = item.get("sugars_g")
            grouped[key]["protein_g"] = item.get("protein_g")
        
        allergens_str = item.get("allergens", "").strip()
        if allergens_str:
            allergens_list = [a.strip() for a in allergens_str.split(",") if a.strip()]
            grouped[key]["allergens"].update(allergens_list)
        
        # Handle ingredients
        ingredients_str = item.get("ingredients", "").strip()
        if ingredients_str:
            # Split by comma, but be careful about commas inside parentheses if any
            # For now, simple split is better than nothing
            ingredients_list = [i.strip() for i in ingredients_str.split(",") if i.strip()]
            grouped[key]["ingredients"].update(ingredients_list)
        
        if item.get("diets"):
            grouped[key]["diet_types"].update(item["diets"])
        
        meal = item.get("meal", "").strip()
        if meal:
            grouped[key]["availability_today"].add(meal.lower())
    
    result = []
    for data in grouped.values():
        result.append({
            "item": data["item"],
            "dining_hall": data["dining_hall"],
            "calories": data["calories"],
            "serving_size": data["serving_size"],
            "fat_g": data["fat_g"],
            "sat_fat_g": data["sat_fat_g"],
            "trans_fat_g": data["trans_fat_g"],
            "cholesterol_mg": data["cholesterol_mg"],
            "sodium_mg": data["sodium_mg"],
            "carbs_g": data["carbs_g"],
            "fiber_g": data["fiber_g"],
            "sugars_g": data["sugars_g"],
            "protein_g": data["protein_g"],
            "allergens": list(data["allergens"]) if data["allergens"] else None,
            "diet_types": list(data["diet_types"]) if data["diet_types"] else None,
            "availability_today": list(data["availability_today"]) if data["availability_today"] else None,
            "ingredients": list(data["ingredients"]) if data["ingredients"] else None,
        })
    
    return result

def init_database():
    """
    Main initialization function.
    
    Scrapes menus, processes the data, and updates or inserts records into the DB.
    """
    db = SessionLocal()
    try:
        scraped_items = scrape_all_menus()
        if not scraped_items:
            return

        mapped_items = map_scraper_data_to_schema(scraped_items)
        added_count = 0
        updated_count = 0
        today = datetime.now().date()

        for item_data in mapped_items:
            existing_item = db.query(DiningHallMenu).filter(
                DiningHallMenu.item == item_data["item"],
                DiningHallMenu.dining_hall == item_data["dining_hall"]
            ).first()

            if existing_item:
                for key, value in item_data.items():
                    setattr(existing_item, key, value)
                existing_item.last_updated = today
                updated_count += 1
            else:
                new_item = DiningHallMenu(**item_data)
                new_item.last_updated = today
                db.add(new_item)
                added_count += 1

        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()