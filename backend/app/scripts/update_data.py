import logging
import sys
from pathlib import Path

# Add backend to path so imports work
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.init_db import init_database
from app.scripts.backfill_embeddings import main as backfill_embeddings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_update_cycle():
    """Runs the full data pipeline: Scrape -> Clean -> Embed"""
    logger.info("🚀 Starting scheduled data update...")
    
    try:
        # 1. Scrape data and update SQL Database
        logger.info("Step 1: Scraping menus...")
        init_database()
        logger.info("✅ Database updated.")

        # 2. Generate Embeddings for new items
        logger.info("Step 2: Backfilling embeddings...")
        backfill_embeddings(batch_size=50)
        logger.info("✅ Embeddings backfilled.")
        
    except Exception as e:
        logger.error(f"❌ Error during update cycle: {e}")
        raise e

if __name__ == "__main__":
    run_update_cycle()
