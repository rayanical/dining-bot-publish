#!/usr/bin/env python3
"""
Backfill script to populate embeddings for existing menu items.

Usage:
    cd backend
    python -m app.scripts.backfill_embeddings

This script will:
1. Find all menu items without embeddings
2. Build embedding text from item name + ingredients (infer if missing)
3. Generate embeddings in batches via OpenAI
4. Update the database with the new embeddings
"""

import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from typing import List, Tuple
from tqdm import tqdm
from sqlalchemy import text
from app.core.database import SessionLocal
from app.models import DiningHallMenu, PGVECTOR_AVAILABLE
from app.core.embeddings import (
    get_embeddings_batch,
    build_embedding_text,
)


def get_items_without_embeddings(db) -> List[DiningHallMenu]:
    """
    Get all menu items that don't have embeddings yet.
    
    Args:
        db (Session): Database session.

    Returns:
        List[DiningHallMenu]: List of items needing embeddings.
    """
    if not PGVECTOR_AVAILABLE:
        # If pgvector not available, just get all items
        return db.query(DiningHallMenu).all()
    
    # Get items where embedding is NULL AND ingredients are present
    # We only want to embed items that have valid ingredient data
    return db.query(DiningHallMenu).filter(
        DiningHallMenu.embedding == None,
        DiningHallMenu.ingredients != None
    ).all()


def prepare_items_for_embedding(
    items: List[DiningHallMenu]
) -> List[Tuple[int, str]]:
    """
    Prepare item IDs and embedding texts.
    
    Args:
        items (List[DiningHallMenu]): List of items to process.

    Returns:
        List[Tuple[int, str]]: list of (item_id, embedding_text) tuples.
    """
    prepared = []
    
    for item in tqdm(items, desc="Preparing items"):
        ingredients = item.ingredients
        
        if not ingredients:
            # Skip items without ingredients (should be filtered by query anyway)
            continue
        
        text = build_embedding_text(item.item, ingredients)
        prepared.append((item.id, text))
    
    return prepared


def update_embeddings_batch(
    db, item_ids: List[int], embeddings: List[List[float]]
) -> int:
    """
    Update embeddings in the database.
    
    Args:
        db (Session): Database session.
        item_ids (List[int]): List of IDs to update.
        embeddings (List[List[float]]): List of embedding vectors.

    Returns:
        int: Number of rows updated.
    """
    if not PGVECTOR_AVAILABLE:
        print("Warning: pgvector not available, skipping embedding storage")
        return 0
    
    updated = 0
    for item_id, embedding in zip(item_ids, embeddings):
        try:
            # Use raw SQL for pgvector update
            # Fix: Use CAST(:embedding AS vector) instead of ::vector to avoid SQLAlchemy parser issues
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            db.execute(
                text(
                    "UPDATE dining_hall_menu SET embedding = CAST(:embedding AS vector) WHERE id = :id"
                ),
                {"embedding": embedding_str, "id": item_id},
            )
            updated += 1
        except Exception as e:
            print(f"Error updating item {item_id}: {e}")
    
    db.commit()
    return updated


def update_ingredients_batch(
    db, items_with_ingredients: List[Tuple[int, List[str]]]
) -> int:
    """
    Update ingredients in the database.
    
    Args:
        db (Session): Database session.
        items_with_ingredients (List[Tuple]): List of (id, ingredients) tuples.

    Returns:
        int: Number of rows updated.
    """
    updated = 0
    for item_id, ingredients in items_with_ingredients:
        try:
            item = db.query(DiningHallMenu).filter(DiningHallMenu.id == item_id).first()
            if item and not item.ingredients:
                item.ingredients = ingredients
                updated += 1
        except Exception as e:
            print(f"Error updating ingredients for item {item_id}: {e}")
    
    db.commit()
    return updated


def main(
    batch_size: int = 50,
):
    """
    Main backfill execution function.
    
    Args:
        batch_size (int): Size of batches sent to OpenAI.
    """
    print("=" * 60)
    print("Embedding Backfill Script")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 1. Find items
        print("\n1. Finding items without embeddings...")
        items = get_items_without_embeddings(db)
        print(f"   Found {len(items)} items to process")
        
        if not items:
            print("\n✅ All items already have embeddings!")
            return
        
        # 2. Prepare text
        print("\n2. Preparing embedding texts...")
        prepared_items = prepare_items_for_embedding(items)
        
        if not prepared_items:
            print("   No items prepared (maybe missing ingredients?)")
            return

        # 3. Generate and update in batches
        print(f"\n3. Generating embeddings (Batch size: {batch_size})...")
        
        total_updated = 0
        
        # Process in chunks
        for i in range(0, len(prepared_items), batch_size):
            batch = prepared_items[i : i + batch_size]
            batch_ids = [item[0] for item in batch]
            batch_texts = [item[1] for item in batch]
            
            print(f"   Processing batch {i//batch_size + 1} ({len(batch)} items)...")
            
            # Generate embeddings
            embeddings = get_embeddings_batch(batch_texts)
            
            # Update database
            updated = update_embeddings_batch(db, batch_ids, embeddings)
            total_updated += updated;
        
        print(f"\n   Updated {total_updated} items with embeddings")
        
        print("\n" + "=" * 60)
        print("✅ Backfill complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during backfill: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill embeddings for menu items")
    parser.add_argument(
        "--batch-size", type=int, default=50, help="Batch size for embedding API calls"
    )
    parser.add_argument(
        "--no-infer",
        action="store_true",
        help="Don't infer ingredients for items missing them",
    )
    parser.add_argument(
        "--no-save-ingredients",
        action="store_true",
        help="Don't save inferred ingredients to database",
    )
    
    args = parser.parse_args()
    
    main(
        batch_size=args.batch_size,
    )