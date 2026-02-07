# Hacketon - Database Schema & Matching Algorithm Foundation

This project implements a MongoDB-based database schema and semantic matching algorithm using Google's Gemini API for embeddings.

## Project Structure

```
backend/
├── config/
│   └── database.py          # MongoDB connection setup
├── models/
│   ├── __init__.py
│   ├── user.py              # User model with Pydantic/MongoDB schemas
│   ├── pod.py               # Pod model
│   └── message.py           # Message model
├── services/
│   ├── __init__.py
│   ├── gemini_service.py    # Gemini API wrapper for embeddings & chat
│   └── matching_service.py  # Core matching algorithm logic
└── utils/
    ├── __init__.py
    └── embeddings.py        # Helper functions for vector operations
tests/
├── __init__.py
├── test_database.py         # Database connection and CRUD tests
├── test_embeddings.py       # Embedding and cosine similarity tests
└── test_matching.py         # Matching algorithm tests
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up MongoDB:**
   - Install MongoDB Community: https://www.mongodb.com/try/download/community
   - Start MongoDB: `mongod` (or `net start MongoDB` on Windows)
   - Verify: `python scripts/check_db.py`

3. **Configure environment variables:**
   Copy `.env.example` to `.env` and set:
   ```
   MONGODB_URI=mongodb://localhost:27017/hacketon
   JWT_SECRET_KEY=your-secret-key-change-in-production
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

## Database Schema

### Users Collection
- `_id`: ObjectId
- `username`: string (unique, required)
- `email`: string (unique, required)
- `password_hash`: string (required)
- `created_at`: datetime
- `active_pod_id`: ObjectId (nullable)
- `profile`: object
  - `interests`: array of strings
  - `work_area`: string
  - `current_goals`: array of strings
  - `struggles`: array of strings
- `matching_preferences`: object
  - `match_type`: enum ("friendship", "goal", "issues")
  - `current_focus_text`: string
  - `focus_embedding`: array of floats (Gemini embedding vector)
  - `last_updated`: datetime

### Pods Collection
- `_id`: ObjectId
- `pod_type`: enum ("friendship", "goal", "issues")
- `members`: array of ObjectIds (max 3)
- `created_at`: datetime
- `expires_at`: datetime (48 hours from creation)
- `is_active`: boolean
- `gemini_icebreaker`: string
- `focus_context`: string

### Messages Collection
- `_id`: ObjectId
- `pod_id`: ObjectId (reference to Pods)
- `sender_id`: ObjectId (reference to Users)
- `content`: string
- `timestamp`: datetime
- `read_by`: array of ObjectIds

## Matching Algorithm

The `find_matches()` function in `MatchingService`:

1. Accepts `user_id`, `match_type`, and `focus_text`
2. Generates a Gemini embedding for the `focus_text`
3. Stores the embedding in the user's `matching_preferences.focus_embedding`
4. Queries MongoDB for candidates with:
   - Same `match_type`
   - No active pod (`active_pod_id` is null)
   - Different `_id` from current user
   - Valid `focus_embedding`
5. Calculates cosine similarity between user's embedding and all candidate embeddings
6. Returns top 4 matches sorted by similarity score (descending)

## Gemini Service

The `GeminiService` provides:
- `get_embedding(text)`: Generates embeddings using `models/embedding-001`
- `generate_icebreaker(user_profiles, match_type)`: Generates icebreaker text using `gemini-1.5-pro`

## Testing

All tests use mocked API calls to avoid external dependencies during testing. Run tests with:

```bash
pytest
```

Test coverage includes:
- Database connection and CRUD operations
- Embedding generation and cosine similarity calculations
- Matching algorithm with various edge cases (no matches, less than 4 matches, etc.)

