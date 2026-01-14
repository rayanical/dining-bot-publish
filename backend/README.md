# ⚙️ Dining Bot Backend

A FastAPI service that powers the intelligence of the Dining Bot. It manages data scraping, nutrition calculations, and the RAG pipeline that combines Semantic Search (pgvector) with Text-to-SQL generation.

## ⚡ Tech Stack

-   **Framework:** FastAPI
-   **Database:** PostgreSQL (via Supabase), SQLAlchemy ORM
-   **AI/LLM:** OpenAI (GPT-4o-mini), `pgvector` for embeddings
-   **Scraping:** BeautifulSoup4, Requests
-   **Language:** Python 3.8+

## 🛠️ Setup & Installation

### 1. Create Virtual Environment

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Connection string to your Supabase PostgreSQL DB
DATABASE_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres

# OpenAI API Key for RAG and Chat
OPENAI_API_KEY=sk-...
```

### 4. Initialize Database & Scrape Menus

This script creates tables and scrapes the latest data from the UMass Dining website.

```bash
python -m app.core.init_db
```

_(Optional) To backfill embeddings for semantic search:_

```bash
python -m app.scripts.backfill_embeddings
```

### 5. Run Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
API Documentation (Swagger UI) is available at `http://localhost:8000/docs`.

## 🧠 Core Features

-   **`app/core/scraper.py`**: Scrapes UMass dining websites and normalizes nutrition data.
-   **`app/core/rag.py`**: The main Retrieval Augmented Generation pipeline.
-   **`app/core/text_to_sql.py`**: Converts natural language queries (e.g., "high protein dinner") into SQL queries for precise database lookup.
-   **`app/core/semantic_retrieval.py`**: Uses vector embeddings to find items based on meaning (e.g., matching "comfort food" to "Mac and Cheese").
-   **`app/api/routes/meal_builder.py`**: Logic for generating combinations of food items to meet specific macro targets.

## 📂 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic schemas for API validation
│   ├── api/
│   │   └── routes/          # API endpoint definitions
│   │       ├── chat.py      # Chat/RAG endpoints
│   │       ├── food.py      # Food search endpoints
│   │       ├── meal_builder.py  # Meal planning endpoints
│   │       └── users.py     # User profile endpoints
│   ├── core/
│   │   ├── config.py        # Environment configuration
│   │   ├── database.py      # Database connection & session management
│   │   ├── scraper.py       # Web scraping logic
│   │   ├── embeddings.py    # OpenAI embedding generation
│   │   ├── query_parser.py  # LLM-based semantic router
│   │   ├── retrieval.py     # Main retrieval orchestration
│   │   ├── text_to_sql.py   # Natural language to SQL conversion
│   │   ├── semantic_retrieval.py  # Vector search with pgvector
│   │   └── rag.py           # RAG pipeline coordinator
│   └── scripts/
│       └── backfill_embeddings.py  # Generate embeddings for existing data
├── requirements.txt
└── .env
```

## 🔧 Development

### Running Tests

```bash
pytest
```

## 📝 API Endpoints

-   `POST /api/chat/` - Streaming chat with RAG
-   `POST /api/food/search` - Search menu items
-   `POST /api/meal-builder/generate` - Generate meal plans
-   `GET /api/users/profile` - Get user profile
-   `POST /api/users/log-food` - Log a meal

See `http://localhost:8000/docs` for interactive API documentation.
