"""
Chat API Routes.

This module provides the endpoints for the AI chat interface, handling
request validation, history parsing, and response streaming.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.rag import rag_answer_stream
from fastapi.responses import StreamingResponse

router = APIRouter()

class ManualFilters(BaseModel):
    """
    User-selected filters from the frontend UI.
    
    Attributes:
        dining_halls (List[str]): List of halls to filter by (e.g. ["Worcester"]).
        meals (List[str]): List of meals to filter by (e.g. ["Lunch"]).
    """
    dining_halls: Optional[List[str]] = None
    meals: Optional[List[str]] = None

class ChatRequest(BaseModel):
    """
    Incoming chat request payload.
    
    Attributes:
        query (str): Simple string query (optional).
        messages (List[Dict]): Full chat history from AI SDK (optional).
        user_id (str): The requesting user's ID.
        filters (ManualFilters): UI-applied filters.
    """
    # Either a plain query or full UI messages from the frontend AI SDK
    query: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    user_id: Optional[str] = None
    filters: Optional[ManualFilters] = None  # Manual UI-selected filters

def get_db():
    """Dependency to provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Streaming chat endpoint that yields text chunks.
    
    This endpoint processes the user's natural language query, retrieves relevant
    menu data, and streams back an AI-generated response.

    Args:
        req (ChatRequest): The request payload containing query/messages and filters.
        db (Session): Database session dependency.

    Returns:
        StreamingResponse: A text stream of the AI's response.
    
    Raises:
        HTTPException: If query parsing fails or input is empty.
    """
    # Debug: log the user_id and filters being received
    print(f"[Chat] Received request with user_id: {req.user_id}, filters: {req.filters}")
    
    query: Optional[str] = None
    history_text: Optional[str] = None
    
    # Convert manual filters to dict for downstream use
    manual_filters: Optional[Dict[str, Any]] = None
    if req.filters:
        manual_filters = {}
        if req.filters.dining_halls:
            manual_filters["dining_halls"] = req.filters.dining_halls
        if req.filters.meals:
            manual_filters["meals"] = req.filters.meals

    # Prefer messages if provided; otherwise fall back to query
    if req.messages:
        # Extract last user message text and build a short textual history
        msgs = req.messages
        # Find last user message for the query
        last_user = next((m for m in reversed(msgs) if m.get("role") == "user"), None)
        if last_user:
            parts = last_user.get("parts") or []
            user_texts = [p.get("text", "") for p in parts if isinstance(p, dict) and p.get("type") == "text"]
            query = "".join(user_texts).strip()

        # Build concise history from prior messages (limit to recent 6 total)
        prior = msgs[:-1][-6:] if len(msgs) > 1 else []
        lines: List[str] = []
        for m in prior:
            role = m.get("role", "assistant")
            parts = m.get("parts") or []
            text = "".join([p.get("text", "") for p in parts if isinstance(p, dict) and p.get("type") == "text"]).strip()
            if text:
                lines.append(f"{role.capitalize()}: {text}")
        history_text = "\n".join(lines) if lines else None

    if query is None:
        query = (req.query or "").strip()

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        stream_gen = rag_answer_stream(query, db, user_id=req.user_id, history_text=history_text, manual_filters=manual_filters, current_date=date.today())
        return StreamingResponse(stream_gen, media_type="text/plain")
    except Exception as e:
        return StreamingResponse(iter([f"Error processing query: {str(e)}"]), media_type="text/plain", status_code=500)