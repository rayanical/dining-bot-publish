---
title: Dining Bot
emoji: 🍱
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
app_port: 7860
---
# UMass Dining Bot 🍽️

An AI-powered nutrition assistant for the UMass Amherst dining experience. This application helps students navigate dining halls by providing personalized meal recommendations, tracking macros, and answering natural language queries about menus using a RAG (Retrieval-Augmented Generation) pipeline.

## 🌟 Key Features

-   **AI Chat Assistant:** Ask questions like "Where can I find high-protein vegan food?" and get answers based on real-time menu data.
-   **Meal Builder:** Algorithmically generates meal plans (Protein Focus, Balanced, Low Carb) to fill your daily nutritional gaps.
-   **Smart Food Logging:** Log meals directly from search results or recommendations to track calories and protein against your goals.
-   **Personalized Profile:** Filters menus based on your dietary restrictions (Vegan, Halal, Gluten-Free) and allergens.
-   **Comprehensive Dashboard:** Showcases dietary goals and progress, logged and saved safely and accessibly.

## 🏗️ Architecture

The project acts as a monorepo with two distinct services:

1. **Frontend (Next.js):** Handles user UI, authentication, and chat streaming.
2. **Backend (FastAPI):** Handles database logic, web scraping, RAG pipeline (Vector Search + Text-to-SQL), and LLM interaction.
3. **Database (Supabase/PostgreSQL):** Stores user profiles, logs, and scraped menu items with vector embeddings.

## 🚀 Quick Start

### Prerequisites

-   Node.js 18+ & Bun (or npm/yarn)
-   Python 3.10+
-   A Supabase project (PostgreSQL)
-   OpenAI API Key

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/dining-bot.git
cd dining-bot
```

### 2. Backend Setup

Navigate to the `backend` folder and follow the [Backend README](./backend/README.md) to start the API server on port `8000`.

### 3. Frontend Setup

Navigate to the `frontend` folder and follow the [Frontend README](./frontend/README.md) to start the UI on port `3000`.

## 📚 Documentation

-   [Frontend Setup Guide](./frontend/README.md) - Next.js app configuration and UI components
-   [Backend Setup Guide](./backend/README.md) - FastAPI server, RAG pipeline, and database setup
