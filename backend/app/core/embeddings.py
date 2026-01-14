"""
Embedding Utilities.

This module handles interactions with the OpenAI Embeddings API to generate
vectors for menu items. These embeddings are used for semantic search.
"""

from typing import List, Optional
from openai import OpenAI
from app.core.config import OPENAI_API_KEY

_client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def get_embedding(text: str) -> List[float]:
    """
    Generate an embedding vector for the given text.

    Args:
        text (str): The text to embed (e.g., item name + ingredients).

    Returns:
        List[float]: A list of floats representing the embedding vector (1536 dimensions).
    """
    text = text.strip()
    if not text:
        # Return zero vector for empty text
        return [0.0] * EMBEDDING_DIMENSIONS

    response = _client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def get_embeddings_batch(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batches.

    Args:
        texts (List[str]): List of texts to embed.
        batch_size (int): Number of texts to embed per API call (max 2048).

    Returns:
        List[List[float]]: List of embedding vectors in the same order as input texts.
    """
    all_embeddings: List[List[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        # Clean and handle empty strings
        batch = [t.strip() if t.strip() else " " for t in batch]

        response = _client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
        )
        # Sort by index to ensure order matches input
        sorted_data = sorted(response.data, key=lambda x: x.index)
        all_embeddings.extend([d.embedding for d in sorted_data])

    return all_embeddings


def build_embedding_text(item_name: str, ingredients: Optional[List[str]] = None) -> str:
    """
    Build the text representation for embedding a menu item.

    Combines the item name with its ingredients for richer semantic matching.

    Args:
        item_name (str): The name of the menu item.
        ingredients (List[str]): Optional list of ingredients.

    Returns:
        str: A combined text string suitable for embedding.
    """
    parts = [item_name]
    if ingredients:
        parts.append("Ingredients: " + ", ".join(ingredients))
    return " | ".join(parts)


def infer_ingredients_from_name(item_name: str) -> List[str]:
    """
    Use GPT to infer likely ingredients from a menu item name.

    Useful for items that don't have explicit ingredient data available
    from the scraper.

    Args:
        item_name (str): The name of the menu item (e.g., "Grilled Chicken Caesar Salad").

    Returns:
        List[str]: A list of inferred ingredient names.
    """
    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a culinary expert. Given a menu item name, list the most likely "
                        "main ingredients as a comma-separated list. Be concise and only list "
                        "ingredients, not preparation methods. Return ONLY the comma-separated list."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Menu item: {item_name}",
                },
            ],
            temperature=0.2,
            max_tokens=100,
        )
        content = response.choices[0].message.content or ""
        # Parse comma-separated ingredients
        ingredients = [ing.strip().lower() for ing in content.split(",") if ing.strip()]
        return ingredients
    except Exception:
        return []