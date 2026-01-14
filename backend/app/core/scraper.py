"""
Web Scraper Module.

This module is responsible for fetching, parsing, and cleaning menu data
from the UMass Dining website.
"""

import requests
import re
from bs4 import BeautifulSoup

# Configuration
BASE_URL = "https://umassdining.com/locations-menus"
DINING_HALLS = [
    "berkshire",
    "worcester",
    "franklin",
    "hampshire"
]

def clean_numeric_value(s):
    """
    Extract the first numeric (int/float) value embedded in a string.

    Examples:
        "16.4g" -> 16.4
        "199" -> 199.0
        "49.8mg" -> 49.8

    Args:
        s (str | Any): Raw string or value containing digits.

    Returns:
        float: Parsed numeric value, or 0.0 if none found / parse fails.
    """
    if s is None:
        return 0.0
    
    match = re.search(r'[\d\.]+', str(s))
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return 0.0
    return 0.0

def scrape_menu_page(dining_hall_slug):
    """
    Scrape all meals and items for a single dining hall page.

    Args:
        dining_hall_slug (str): Slug portion of the dining hall URL (e.g. "berkshire").

    Returns:
        list[dict]: List of item dictionaries with nutrition, diets, and metadata.
    """
    url = f"{BASE_URL}/{dining_hall_slug}/menu"

    try:
        page = requests.get(url)
        page.raise_for_status()
    except requests.exceptions.RequestException:
        return []

    soup = BeautifulSoup(page.text, 'html.parser')
    all_food_items = []
    
    title = soup.find("title").text
    dining_hall_name = title.split("|")[0].strip().replace(" Menu", "")
    
    panel_container = soup.find("div", class_="panel-container")
    if not panel_container:
        return []
    
    meal_panels = panel_container.find_all("div", recursive=False)
    
    for panel in meal_panels:
        meal_name_tag = panel.find("h2")
        if not meal_name_tag:
            continue
        meal_name = meal_name_tag.text.strip()
        content_section = panel.find("div", id=re.compile(r"content_text"))
        if not content_section:
            continue

        current_station = "Unknown"
        
        for element in content_section.children:
            if element.name == "h2" and 'menu_category_name' in element.get('class', []):
                current_station = element.text.strip()
            
            elif element.name == "li" and 'lightbox-nutrition' in element.get('class', []):
                item_link = element.find("a")
                if not item_link:
                    continue
                
                data = item_link.attrs
                
                try:
                    diets = data.get('data-clean-diet-str', '').split(', ')
                    
                    food_item = {
                        "name": data.get('data-dish-name'),
                        "dining_hall": dining_hall_name,
                        "meal": meal_name,
                        "station": current_station,
                        "serving_size": data.get('data-serving-size'),
                        "calories": clean_numeric_value(data.get('data-calories')),
                        "fat_g": clean_numeric_value(data.get('data-total-fat')),
                        "sat_fat_g": clean_numeric_value(data.get('data-sat-fat')),
                        "trans_fat_g": clean_numeric_value(data.get('data-trans-fat')),
                        "cholesterol_mg": clean_numeric_value(data.get('data-cholesterol')),
                        "sodium_mg": clean_numeric_value(data.get('data-sodium')),
                        "carbs_g": clean_numeric_value(data.get('data-total-carb')),
                        "fiber_g": clean_numeric_value(data.get('data-dietary-fiber')),
                        "sugars_g": clean_numeric_value(data.get('data-sugars')),
                        "protein_g": clean_numeric_value(data.get('data-protein')),
                        "allergens": data.get('data-allergens', '').strip(),
                        "ingredients": data.get('data-ingredient-list', '').strip(),
                        "diets": [d for d in diets if d]
                    }
                    all_food_items.append(food_item)
                
                except Exception:
                    continue

    return all_food_items


def scrape_all_menus():
    """
    Scrape menus for all configured dining halls and combine results.

    Returns:
        list[dict]: Aggregated list of all items across dining halls.
    """
    master_menu_list = []
    
    for hall_slug in DINING_HALLS:
        items = scrape_menu_page(hall_slug)
        master_menu_list.extend(items)
    return master_menu_list

if __name__ == "__main__":
    scrape_all_menus()