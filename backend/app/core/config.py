"""
App Configuration.

This module loads environment variables from the .env file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment configuration from backend root .env.
backend_dir = Path(__file__).parent.parent.parent
env_path = backend_dir / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
"""str: Connection string for the PostgreSQL database."""

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
"""str: API key for OpenAI services."""