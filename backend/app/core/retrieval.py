import logging
from typing import Dict, List, Optional
from datetime import date
from sqlalchemy import and_, or_, func, String
from sqlalchemy.orm import Session
from app.models import DiningHallMenu, PGVECTOR_AVAILABLE
from app.core.query_parser import ai_parse_query, SearchIntent
from app.core.text_to_sql import text_to_sql_retrieve

logger = logging.getLogger(__name__)

def build_sql_filters(filters: Dict, db: Session, current_date: Optional[date] = None) -> List:
    """
    Build SQLAlchemy filter conditions from parsed query filters.

    Args:
        filters (Dict): Parsed filters (e.g., dining_hall, meal, diets, allergies,
            min_calories, max_calories, item_name).
        db (Session): SQLAlchemy database session.
        current_date (Optional[date]): The current date to filter by. If None, uses today's date.

    Returns:
        List: A list of SQLAlchemy boolean expressions to pass to Query.filter().
    """
    conditions = []
    
    # CRITICAL: Always filter by today's date to avoid stale "ghost" menu items
    filter_date = current_date or date.today()
    conditions.append(DiningHallMenu.last_updated == filter_date)
    
    # --- NEW: Handle Text Search ("item_name") ---
    if filters.get("item_name"):
        search_term = filters["item_name"]
        # Use ilike for case-insensitive matching
        conditions.append(DiningHallMenu.item.ilike(f"%{search_term}%"))
    # ---------------------------------------------

    if filters.get("dining_hall"):
        conditions.append(DiningHallMenu.dining_hall == filters["dining_hall"])
    
    if filters.get("meal"):
        # Meal is already lowercase from query parser to match database format
        meal_filter = filters["meal"].lower()  # Ensure lowercase for safety
        if "postgres" in str(db.bind.url).lower():
            # PostgreSQL: use array_to_string to search in array
            conditions.append(func.array_to_string(DiningHallMenu.availability_today, ',').ilike(f'%{meal_filter}%'))
        else:
            # SQLite fallback
            conditions.append(func.cast(DiningHallMenu.availability_today, String).like(f'%"{meal_filter}"%'))
    
    if filters.get("diets"):
        diet_conditions = []
        db_url = str(db.bind.url).lower()
        
        # Check if we're using PostgreSQL
        is_postgres = "postgres" in db_url
        
        for diet in filters["diets"]:
            if is_postgres:
                # PostgreSQL: Use array_to_string to convert array to string, then search
                diet_conditions.append(func.array_to_string(DiningHallMenu.diet_types, ',').ilike(f'%{diet}%'))
            else:
                # SQLite: ARRAY type doesn't work, so we check using string operations
                diet_conditions.append(
                    func.cast(DiningHallMenu.diet_types, String).like(f'%"{diet}"%')
                    if hasattr(func, 'cast')
                    else func.array_to_string(DiningHallMenu.diet_types, ',').ilike(f'%{diet}%')
                )
        
        if diet_conditions:
            try:
                conditions.append(or_(*diet_conditions))
            except Exception:
                for condition in diet_conditions:
                    conditions.append(condition)
    
    if filters.get("allergies"):
        for allergen in filters["allergies"]:
            if "postgres" in str(db.bind.url).lower():
                # PostgreSQL: Use array_to_string to search, then negate
                conditions.append(~func.array_to_string(DiningHallMenu.allergens, ',').ilike(f'%{allergen}%'))
            else:
                conditions.append(~func.cast(DiningHallMenu.allergens, String).like(f'%"{allergen}"%'))
    
    if filters.get("min_calories") is not None:
        conditions.append(DiningHallMenu.calories >= filters["min_calories"])
    if filters.get("max_calories") is not None:
        conditions.append(DiningHallMenu.calories <= filters["max_calories"])
    
    return conditions


def _intent_filters_to_dict(intent: SearchIntent) -> Dict:
    """Flatten SearchIntent.filters into a dict compatible with downstream retrievers."""
    # Null-safety: ensure filters object exists
    from app.core.query_parser import SearchFilters
    f = intent.filters or SearchFilters()
    
    nc = f.nutritional_constraints or {}
    dining_halls = f.dining_halls or []
    meals = f.meals or []
    dietary_restrictions = f.dietary_restrictions or []
    allergens_to_exclude = f.allergens_to_exclude or []
    
    primary_hall = dining_halls[0] if dining_halls else None
    primary_meal = meals[0] if meals else None
    
    return {
        "dining_halls": dining_halls,
        "meals": meals,
        "dining_hall": primary_hall,
        "meal": primary_meal,
        "dietary_restrictions": dietary_restrictions,
        "allergens_to_exclude": allergens_to_exclude,
        # Backward compatibility aliases
        "diets": dietary_restrictions,
        "allergies": allergens_to_exclude,
        "min_calories": nc.get("min_calories"),
        "max_calories": nc.get("max_calories"),
        "min_protein": nc.get("min_protein"),
        "max_protein": nc.get("max_protein"),
        "sort_by": f.sort_by,
        "search_query": intent.search_query,
        "item_name": None,
    }


def retrieve_food_items(
    query: str,
    db: Session,
    user_profile: Optional[Dict] = None,
    limit: int = 10,
    order_by: str = "calories",
    use_hybrid: bool = True,
    structured_filters: Optional[Dict] = None,
    manual_filters: Optional[Dict] = None,
    current_date: Optional[date] = None,
) -> List[DiningHallMenu]:
    """
    Retrieve relevant menu items based on a natural language query.

    Coordinates between hybrid semantic retrieval and legacy keyword retrieval.

    Args:
        query (str): User's natural language question.
        db (Session): SQLAlchemy database session.
        user_profile (Optional[Dict]): Optional user profile influencing filters.
        limit (int): Maximum number of rows to return.
        order_by (str): Field to order by.
        use_hybrid (bool): Whether to use the hybrid retrieval approach.
        structured_filters (Optional[Dict]): Manual UI-selected filters (dining_hall, meal, item_name)
            that override or augment the parsed query.
        manual_filters (Optional[Dict]): Alias for structured_filters (legacy support).
        current_date (Optional[date]): Date to filter by.

    Returns:
        List[DiningHallMenu]: The list of matching menu rows.
    """
    
    # Prefer explicit manual_filters if provided; keep structured_filters for backward compatibility
    if manual_filters and not structured_filters:
        structured_filters = manual_filters

    try:
        intent: SearchIntent = ai_parse_query(query, user_profile)
    except Exception as e:  # should rarely hit because ai_parse_query already falls back
        logger.error(f"ai_parse_query failed unexpectedly: {e}", exc_info=True)
        return _legacy_retrieve(query, db, user_profile, limit, order_by, structured_filters, current_date)

    intent_filters = _intent_filters_to_dict(intent)
    logger.info(f"Parsed intent: {intent.intent_type}, filters: {intent_filters}")

    # Allow UI/manual overrides to take precedence
    if structured_filters:
        intent_filters.update({k: v for k, v in structured_filters.items() if v})
        logger.debug(f"Applied manual filter overrides: {structured_filters}")

    # Simple bypass: if user explicitly provided item_name or a single hall, do a direct SQL lookup
    if intent_filters.get("item_name") or intent_filters.get("dining_hall"):
        logger.info("Using legacy retrieve for direct item/hall lookup")
        return _legacy_retrieve(query, db, user_profile, limit, order_by, intent_filters, current_date)

    # Route based on intent
    if intent.intent_type == "factual_lookup":
        logger.info("Routing to text-to-SQL (factual_lookup intent)")
        try:
            items, err = text_to_sql_retrieve(
                query=intent.search_query or query,
                db=db,
                user_profile=user_profile,
                manual_filters=intent_filters,
                limit=limit,
            )
            if err:
                logger.warning(f"text_to_sql_retrieve error: {err}")
            else:
                logger.info(f"text-to-SQL returned {len(items)} items")
                return items
        except Exception as e:
            logger.error(f"text_to_sql_retrieve failed, falling back to hybrid: {e}", exc_info=True)

    # hybrid or semantic_search paths
    if use_hybrid:
        try:
            from app.core.semantic_retrieval import hybrid_retrieve

            results = hybrid_retrieve(
                query=intent.search_query or query,
                db=db,
                user_profile=user_profile,
                limit=limit,
                use_semantic=PGVECTOR_AVAILABLE,
                use_text_to_sql=True,
                manual_filters=intent_filters,
                current_date=current_date,
            )
            if results:
                return results
        except Exception as e:
            logger.error(f"Hybrid retrieval failed, falling back to legacy: {e}", exc_info=True)

    return _legacy_retrieve(query, db, user_profile, limit, order_by, intent_filters, current_date)


def _legacy_retrieve(
    query: str,
    db: Session,
    user_profile: Optional[Dict] = None,
    limit: int = 10,
    order_by: str = "calories",
    structured_filters: Optional[Dict] = None,
    current_date: Optional[date] = None,
) -> List[DiningHallMenu]:
    """
    Legacy retrieval using regex-parsed filters and SQLAlchemy queries.
    
    Kept as fallback when hybrid retrieval fails or is disabled.

    Args:
        query (str): The search query.
        db (Session): Database session.
        user_profile (Optional[Dict]): User preference profile.
        limit (int): Results limit.
        order_by (str): Sorting criterion.
        structured_filters (Optional[Dict]): Filters to apply.
        current_date (Optional[date]): Filter date.

    Returns:
        List[DiningHallMenu]: List of items.
    """
    try:
        intent = ai_parse_query(query, user_profile)
        filters = _intent_filters_to_dict(intent)
        mapped_filters = {
            "dining_hall": filters.get("dining_halls", [None])[0] if filters.get("dining_halls") else None,
            "meal": filters.get("meals", [None])[0] if filters.get("meals") else None,
            "diets": filters.get("dietary_restrictions") or [],
            "allergies": filters.get("allergens_to_exclude") or [],
            "min_calories": filters.get("min_calories"),
            "max_calories": filters.get("max_calories"),
            "item_name": filters.get("search_query"),
        }
    except Exception:
        mapped_filters = _legacy_parse_user_query(query, user_profile)

    # Merge structured filters into parsed filters
    if structured_filters:
        for k, v in structured_filters.items():
            if v is not None:
                mapped_filters[k] = v

    conditions = build_sql_filters(mapped_filters, db, current_date)
    q = db.query(DiningHallMenu)
    if conditions:
        q = q.filter(and_(*conditions))
    
    # Order by logic
    if mapped_filters.get("sort_by") == "protein_desc":
        q = q.order_by(func.coalesce(DiningHallMenu.protein_g, 0).desc())
    else:
        query_lower = query.lower()
        if "best" in query_lower or "top" in query_lower or "highest" in query_lower:
            if "calorie" in query_lower and "low" in query_lower:
                q = q.order_by(DiningHallMenu.calories.asc())
            elif "calorie" in query_lower:
                q = q.order_by(DiningHallMenu.calories.desc())
            else:
                q = q.order_by(DiningHallMenu.item.asc())
        else:
            q = q.order_by(DiningHallMenu.dining_hall.asc(), DiningHallMenu.item.asc())
    
    items = q.limit(limit).all()
    
    return items