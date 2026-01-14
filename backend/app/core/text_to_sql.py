"""
Text-to-SQL Generation.

This module converts natural language queries into executable SQL queries using GPT.
It includes rigorous sanitization to prevent SQL injection and unsafe operations.
"""

import re
import logging
from typing import Optional, List, Tuple, Dict
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import OPENAI_API_KEY
from app.models import DiningHallMenu

logger = logging.getLogger(__name__)
_client = OpenAI(api_key=OPENAI_API_KEY)

# Schema description for GPT to understand the database structure
SCHEMA_PROMPT = """You are a SQL query generator for a university dining hall menu database.

TABLE: dining_hall_menu
COLUMNS:
- id: integer (primary key)
- item: text (food name, e.g., "Grilled Chicken Breast", "Caesar Salad")
- dining_hall: text (one of: "Berkshire", "Worcester", "Franklin", "Hampshire")
- last_updated: date
- calories: float (can be NULL)
- serving_size: text
- fat_g: float
- sat_fat_g: float
- trans_fat_g: float
- cholesterol_mg: float
- sodium_mg: float
- carbs_g: float
- fiber_g: float
- sugars_g: float
- protein_g: float
- allergens: text[] (array, e.g., ARRAY['Milk', 'Eggs', 'Wheat'])
- diet_types: text[] (array, e.g., ARRAY['Vegan', 'Vegetarian', 'Halal', 'Kosher'])
- availability_today: text[] (array, e.g., ARRAY['breakfast', 'lunch', 'dinner'])
- ingredients: text[] (array of ingredient names, e.g., ARRAY['chicken', 'olive oil', 'garlic'])

POSTGRESQL ARRAY SYNTAX:
- Check if array contains value: 'value' = ANY(column_name)
- Check if arrays overlap: column_name && ARRAY['val1', 'val2']
- Check if array contains all values: column_name @> ARRAY['val1', 'val2']

RULES:
1. Return ONLY a valid PostgreSQL SELECT query - no explanations
2. Use single quotes for strings
3. Use ILIKE for case-insensitive text matching
4. Use = ANY(column) for checking if a value is in an array
5. ALWAYS add LIMIT 25 at the end
6. NEVER use DELETE, UPDATE, DROP, INSERT, TRUNCATE, ALTER, CREATE, or GRANT
7. Only SELECT from dining_hall_menu table
8. For "best" or "highest" queries, use ORDER BY with DESC
9. For "lowest" or "least" queries, use ORDER BY with ASC
10. Handle NULL values with COALESCE when ordering by nullable columns
11. CRITICAL: ALWAYS include "last_updated = CURRENT_DATE" in the WHERE clause to ensure only today's menu items are returned. This is MANDATORY for every query.

EXAMPLES:
User: "vegan lunch options"
SQL: SELECT * FROM dining_hall_menu WHERE last_updated = CURRENT_DATE AND 'Vegan' = ANY(diet_types) AND 'lunch' = ANY(availability_today) LIMIT 25

User: "high protein foods at Worcester"
SQL: SELECT * FROM dining_hall_menu WHERE last_updated = CURRENT_DATE AND dining_hall = 'Worcester' AND protein_g IS NOT NULL ORDER BY protein_g DESC LIMIT 25

User: "something with chicken"
SQL: SELECT * FROM dining_hall_menu WHERE last_updated = CURRENT_DATE AND ('chicken' = ANY(ingredients) OR item ILIKE '%chicken%') LIMIT 25

User: "low calorie breakfast options"
SQL: SELECT * FROM dining_hall_menu WHERE last_updated = CURRENT_DATE AND 'breakfast' = ANY(availability_today) AND calories IS NOT NULL ORDER BY calories ASC LIMIT 25

User: "gluten free options without nuts"
SQL: SELECT * FROM dining_hall_menu WHERE last_updated = CURRENT_DATE AND 'Gluten-Free' = ANY(diet_types) AND NOT ('Tree Nuts' = ANY(allergens) OR 'Peanuts' = ANY(allergens)) LIMIT 25

User: "what's for dinner at Franklin"
SQL: SELECT * FROM dining_hall_menu WHERE last_updated = CURRENT_DATE AND dining_hall = 'Franklin' AND 'dinner' = ANY(availability_today) LIMIT 25
"""

# Forbidden SQL keywords that should never appear in generated queries
FORBIDDEN_KEYWORDS = [
    "DELETE", "UPDATE", "DROP", "INSERT", "TRUNCATE", "ALTER", "CREATE",
    "GRANT", "REVOKE", "EXECUTE", "CALL", "COPY", "VACUUM", "ANALYZE",
    "CLUSTER", "COMMENT", "LOCK", "NOTIFY", "LISTEN", "UNLISTEN",
    "PREPARE", "DEALLOCATE", "SET ", "RESET", "SHOW", "BEGIN", "COMMIT",
    "ROLLBACK", "SAVEPOINT", "RELEASE", "DO ", "DECLARE"
]


def generate_sql(user_query: str, user_profile: Optional[Dict] = None) -> str:
    """
    Generate a SQL query from a natural language question.

    Args:
        user_query (str): The user's natural language question about the menu.
        user_profile (Optional[Dict]): Optional dict with 'diets' and 'allergies' lists.

    Returns:
        str: A sanitized PostgreSQL SELECT query string.

    Raises:
        ValueError: If the generated SQL is invalid or unsafe.
    """
    # Build the user message with dietary constraints if present
    user_message = f"Generate SQL for: {user_query}"
    
    if user_profile:
        constraints = []
        diets = user_profile.get("diets") or []
        allergies = user_profile.get("allergies") or []
        
        if diets:
            constraints.append(f"Required diet types: {', '.join(diets)}")
        if allergies:
            constraints.append(f"Must EXCLUDE items containing these allergens: {', '.join(allergies)}")
        
        if constraints:
            user_message += f"\n\nIMPORTANT USER DIETARY CONSTRAINTS (MUST be included in WHERE clause):\n"
            user_message += "\n".join(f"- {c}" for c in constraints)
            user_message += "\n\nFor diets: use 'DietType' = ANY(diet_types)"
            user_message += "\nFor allergens: use NOT ('Allergen' = ANY(allergens))"
    
    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SCHEMA_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        max_tokens=400,
    )

    sql = response.choices[0].message.content or ""
    logger.debug(f"Text-to-SQL generated: {sql[:200]}..." if len(sql) > 200 else f"Text-to-SQL generated: {sql}")

    return sanitize_sql(sql)


def sanitize_sql(sql: str) -> str:
    """
    Sanitize and validate a SQL query for safety.

    Prevents SQL injection and ensures the query only performs read operations
    on the allowed table.

    Args:
        sql (str): The raw SQL string from GPT.

    Returns:
        str: A cleaned and validated SQL query.

    Raises:
        ValueError: If the SQL contains forbidden keywords or is malformed.
    """
    # Clean up markdown code blocks and whitespace
    sql = sql.strip()
    sql = re.sub(r"^```sql\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"^```\s*", "", sql)
    sql = re.sub(r"\s*```$", "", sql)
    sql = sql.strip().rstrip(";").strip()

    if not sql:
        raise ValueError("Empty SQL query generated")

    # Check for forbidden keywords
    sql_upper = sql.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        # Use word boundary check to avoid false positives
        pattern = r"\b" + re.escape(keyword.strip()) + r"\b"
        if re.search(pattern, sql_upper):
            raise ValueError(f"Forbidden SQL keyword detected: {keyword}")

    # Must start with SELECT
    if not sql_upper.lstrip().startswith("SELECT"):
        raise ValueError("Query must be a SELECT statement")

    # Check for multiple statements (semicolon in middle)
    if ";" in sql:
        raise ValueError("Multiple SQL statements not allowed")

    # Ensure it only queries the allowed table
    if "dining_hall_menu" not in sql.lower():
        raise ValueError("Query must reference dining_hall_menu table")

    # FAILSAFE: Inject date filter if GPT forgot to include it
    # This ensures we never return stale menu items
    sql_lower = sql.lower()
    if "last_updated" not in sql_lower or "current_date" not in sql_lower:
        # Insert the date filter after WHERE (or add WHERE if missing)
        if " where " in sql_lower:
            # Insert after WHERE
            where_pos = sql_lower.find(" where ") + 7
            sql = sql[:where_pos] + "last_updated = CURRENT_DATE AND " + sql[where_pos:]
        else:
            # No WHERE clause - add one before ORDER BY or LIMIT
            if " order by " in sql_lower:
                order_pos = sql_lower.find(" order by ")
                sql = sql[:order_pos] + " WHERE last_updated = CURRENT_DATE" + sql[order_pos:]
            elif " limit " in sql_lower:
                limit_pos = sql_lower.find(" limit ")
                sql = sql[:limit_pos] + " WHERE last_updated = CURRENT_DATE" + sql[limit_pos:]
            else:
                sql = sql + " WHERE last_updated = CURRENT_DATE"

    # Add LIMIT if not present
    if "LIMIT" not in sql_upper:
        sql = sql + " LIMIT 25"

    return sql


def execute_generated_sql(
    sql: str, db: Session
) -> Tuple[List[DiningHallMenu], Optional[str]]:
    """
    Execute a generated SQL query and return matching menu items.

    Args:
        sql (str): A sanitized SQL query string.
        db (Session): SQLAlchemy database session.

    Returns:
        Tuple[List, Optional[str]]: A tuple of (list of DiningHallMenu items, optional error message).
    """
    try:
        # Execute the raw SQL to get IDs
        result = db.execute(text(sql))
        rows = result.fetchall()

        if not rows:
            return [], None

        # Extract IDs from results (assumes first column or id column)
        ids = []
        for row in rows:
            # Try to get id from named column or first column
            if hasattr(row, "id"):
                ids.append(row.id)
            elif hasattr(row, "_mapping") and "id" in row._mapping:
                ids.append(row._mapping["id"])
            elif len(row) > 0:
                ids.append(row[0])

        if not ids:
            return [], None

        # Fetch full ORM objects
        items = db.query(DiningHallMenu).filter(DiningHallMenu.id.in_(ids)).all()
        return items, None

    except Exception as e:
        db.rollback()  # Reset transaction state to prevent cascade failures
        return [], f"SQL execution error: {str(e)}"


def text_to_sql_retrieve(
    query: str,
    db: Session,
    limit: int = 10,
    user_profile: Optional[Dict] = None,
    manual_filters: Optional[Dict] = None,
) -> Tuple[List[DiningHallMenu], Optional[str]]:
    """
    Full pipeline: generate SQL from text and execute it.

    Args:
        query (str): Natural language query from user.
        db (Session): SQLAlchemy database session.
        limit (int): Maximum number of results to return.
        user_profile (Optional[Dict]): Optional dict with 'diets' and 'allergies' for SQL generation.

    Returns:
        Tuple[List, Optional[str]]: A tuple of (list of menu items, optional error message).
    """
    augmented_query = query
    if manual_filters:
        constraints = []
        halls = manual_filters.get("dining_halls") or []
        meals = manual_filters.get("meals") or []
        diets = manual_filters.get("dietary_restrictions") or []
        allergies = manual_filters.get("allergens_to_exclude") or []
        min_cal = manual_filters.get("min_calories")
        max_cal = manual_filters.get("max_calories")
        min_pro = manual_filters.get("min_protein")
        max_pro = manual_filters.get("max_protein")
        if halls:
            constraints.append(f"dining_halls: {', '.join(halls)}")
        if meals:
            constraints.append(f"meals: {', '.join(meals)}")
        if diets:
            constraints.append(f"diets: {', '.join(diets)}")
        if allergies:
            constraints.append(f"exclude allergens: {', '.join(allergies)}")
        if min_cal is not None:
            constraints.append(f"min_calories: {min_cal}")
        if max_cal is not None:
            constraints.append(f"max_calories: {max_cal}")
        if min_pro is not None:
            constraints.append(f"min_protein: {min_pro}")
        if max_pro is not None:
            constraints.append(f"max_protein: {max_pro}")
        if constraints:
            augmented_query = query + "\nConstraints: " + "; ".join(constraints)

    try:
        sql = generate_sql(augmented_query, user_profile=user_profile)
        items, error = execute_generated_sql(sql, db)
        if error:
            return [], error
        return items[:limit], None
    except ValueError as e:
        return [], f"SQL generation error: {str(e)}"
    except Exception as e:
        return [], f"Unexpected error: {str(e)}"