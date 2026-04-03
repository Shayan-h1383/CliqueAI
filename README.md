# cliqueAI

Hacketon is a web application that connects people into small, time-limited groups called pods for shared focus areas. Users sign up, describe what they want to work on or connect about, and the system finds semantically similar people using vector embeddings. They can invite each other, form pods, and chat in real time while the pod is active.

## What it is

The product combines:

- **Accounts and profiles** stored in MongoDB, with preferences and a free-text focus that drives matching.
- **Semantic matching** powered by Google Gemini: user focus text is turned into an embedding vector; candidates with the same match type (goal category) are ranked by cosine similarity so people with meaningfully similar intent surface together.
- **Pods and invitations** so matched users can coordinate and join a pod (small member cap, time-bounded lifetime).
- **Messaging** over HTTP and WebSockets (Flask-SocketIO) for live pod chat.

The **backend** is a Flask API with JWT auth, REST routes for auth, matching, pods, applications, invitations, and messages, plus Socket.IO for realtime updates. The **frontend** is a Vue 3 single-page app (Vite, Pinia, Tailwind CSS) that implements onboarding, matching, invitations, and pod chat against the API.

## How it works

1. A user registers and completes onboarding, choosing a match type (`evolve`, `enjoy`, or `support`) and text that describes their current focus.
2. The backend calls Gemini to embed that focus text and stores the vector on the user for matching.
3. `MatchingService` loads other users with the same match type who are available, computes cosine similarity between embeddings, and returns the top matches.
4. Users send invitations or accept flows as implemented in the invitation and application routes; pods are created with metadata and expiry.
5. Messages are stored in MongoDB and pushed to clients over Socket.IO so everyone in a pod sees new messages without full page reloads.

Configuration is driven by environment variables (see `.env.example`): MongoDB URI, JWT secret, Gemini API key, and CORS origins for the Vue dev server.

## Project structure

```
backend/
├── config/           # MongoDB connection
├── models/           # User, pod, message, invitation, application, etc.
├── routes/           # Flask blueprints (auth, matching, pods, messages, ...)
├── services/         # Gemini, matching, pods, invitations, auth, ...
├── tasks/            # Matching-related jobs
└── utils/            # Embeddings helpers
frontend/
├── src/
│   ├── components/   # Onboarding, matching, messaging, common UI
│   ├── views/        # Pages (login, dashboard, pod chat, ...)
│   ├── stores/       # Pinia stores
│   ├── services/     # API client
│   └── router/
├── vite.config.js    # Dev server proxies /api to Flask
└── package.json
tests/                # pytest suite (mocked external APIs where appropriate)
scripts/              # DB checks, seed data, maintenance scripts
```

## Setup

### Backend

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up MongoDB:**
   - Install [MongoDB Community](https://www.mongodb.com/try/download/community)
   - Start MongoDB: `mongod` (on Windows: `net start MongoDB` if installed as a service)
   - Verify: `python scripts/check_db.py`

3. **Configure environment variables:**  
   Copy `.env.example` to `.env` and set:
   ```
   MONGODB_URI=mongodb://localhost:27017/hacketon
   JWT_SECRET_KEY=your-secret-key-change-in-production
   GEMINI_API_KEY=your_gemini_api_key_here
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000
   ```

4. **Run the API** (from the project root):
   ```bash
   python -m backend.app
   ```
   Defaults to port `5000` unless `PORT` is set. Health check: `GET /health`.

### Frontend

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Run the dev server** (with the backend running):
   ```bash
   npm run dev
   ```
   Vite is configured to proxy `/api` to `http://localhost:5000`. Adjust `frontend/vite.config.js` if your API port differs.

3. **Production build:**
   ```bash
   npm run build
   ```
   Output goes to `frontend/dist/` (ignored by git).

### Tests

```bash
pytest tests/ -v
```

Tests mock external APIs where needed so CI and local runs do not require live Gemini calls.

## Database schema (overview)

### Users

- Identifiers, credentials, profile fields (interests, work area, goals, struggles).
- `matching_preferences`: `match_type` (`evolve` | `enjoy` | `support`), focus text, `focus_embedding` (Gemini vector), timestamps.
- `active_pod_id` when the user is in an active pod.

### Pods

- `pod_type` aligned with match type, member list, creation and expiry times, activity flags, optional Gemini-generated icebreaker and focus context.

### Messages

- Linked to `pod_id` and `sender_id`, content, timestamp, read receipts.

(Exact fields are defined in the Pydantic/Mongo models under `backend/models/`.)

## Matching algorithm

The `find_matches()` flow in `MatchingService`:

1. Takes `user_id`, `match_type`, and `focus_text`.
2. Generates a Gemini embedding for `focus_text` and persists it on the user.
3. Queries candidates with the same `match_type`, valid embeddings, not in an active pod, excluding self.
4. Ranks by cosine similarity and returns the top matches (up to four).

## Gemini usage

`GeminiService` provides embedding generation for matching and can generate icebreaker copy for pods using the configured Gemini models (see `backend/services/gemini_service.py`).
