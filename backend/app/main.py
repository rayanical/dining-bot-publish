import os
"""
Main Application Entry Point.

This module initializes the FastAPI application, configures middleware (CORS),
and registers all API routers. It serves as the central hub for the backend service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import chat, users, food, meal_builder

app = FastAPI(title="Dining Bot API")
"""
FastAPI: The main application instance.
"""

app.add_middleware(
    CORSMiddleware,
    # CHANGE THIS: Allow your Vercel app (or "*" for all)
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Only include test routes in development mode
if os.getenv("DEV_MODE", "0") == "1":
    from app.api.routes import test
    app.include_router(test.router, prefix="/api/test", tags=["Test"])

app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(food.router, prefix="/api/food", tags=["Food"])
app.include_router(meal_builder.router, prefix="/api/meal-builder", tags=["Meal Builder"])

@app.get("/")
def root():
    """
    Root endpoint to verify the API is running.

    Returns:
        dict: A simple status message confirming the API is active.
    """
    return {"message": "Dining Bot API is running!"}