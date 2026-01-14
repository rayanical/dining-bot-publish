"""
Database Connection Setup.

This module initializes the SQLAlchemy engine and session factories.
"""

import os
import threading
import logging
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Load environment variables from backend/.env (relative to this file)
backend_dir = Path(__file__).resolve().parents[2]
env_path = backend_dir / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is missing! "
        "If you are on Hugging Face, go to Settings -> Secrets and add DATABASE_URL. "
        "If you are local, make sure your .env file exists."
    )

engine = create_engine(DATABASE_URL)
"""SQLAlchemy Engine instance."""

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""Session factory for creating new database sessions."""

Base = declarative_base()
"""Base class for all ORM models."""
