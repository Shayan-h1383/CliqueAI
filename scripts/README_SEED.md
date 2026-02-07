# Seed Profiles: JSON → Embeddings → Database

## Overview

This document explains how user profiles are converted from JSON to embedding vectors and stored in the database for semantic matching.

---

## 1. JSON Structure (`scripts/seed_profiles.json`)

Each profile has:

| Field | Description | Example |
|-------|-------------|---------|
| `username` | Display name (unique) | `"Alex"` |
| `details` | Bio/description, 200–300 chars | Long paragraph about background |
| `goal` | Short goal text (~50 chars), maps to `third_field` | `"Launch freelance consultancy"` |
| `area` | Area of interest; must match `matching_goal` | `"business"`, `"gaming"`, `"addiction"` |
| `matching_goal` | `evolve` / `enjoy` / `support` | `"evolve"` |
| `city` | City for same-city matching | `"Berlin"` |

**Area values by goal:**
- **evolve**: `studies`, `business`, `arts development`, `sports`, `general`
- **enjoy**: `gaming`, `content`, `humour`, `hiking`, `camping`, `sports`
- **support**: `addiction`, `relationship`, `grief`, `illness`, `general depression`, `other`

---

## 2. Converting JSON → Embeddings

### Embedding text construction

The text passed to Gemini for embedding must match the production flow in `application_matching_service._payload_to_embedding_text`:

```
goal + " " + area + " " + details + " " + third_field + " " + city
```

- `goal` = `matching_goal` (evolve / enjoy / support)
- `area` = area of interest
- `details` = full bio
- `third_field` = `goal` from JSON (short goal)
- `city` = city

### API call (Gemini)

1. Model: `models/gemini-embedding-001`
2. Input: the concatenated text above
3. Output: **768-dimensional float vector** (required for `CliqueApplication` schema)

```python
vector = gemini.get_embedding(text)  # returns List[float], len 768
```

---

## 3. Storing in the Database

### Documents created per profile

1. **User** (`users` collection)
   - `username`, `email`, `password_hash`
   - Email format: `seed_{username}@example.com`
   - Password: `SeedPass123!` (same for all seed users)

2. **CliqueApplication** (`clique_applications` collection)
   - `user_id`: ObjectId of the created user
   - `filter`: `{ "goal": matching_goal, "city": city }`
   - `vector`: 768-dim embedding from Gemini
   - `payload`: `{ goal, area, details, third_field, city }`
   - `status`: `"pending"` (default)

### Matching behavior

- All applications participate in matching (no source/non-source distinction).
- New applicants are embedded with the same text construction.
- Matching uses the same `filter.goal` and `filter.city` (hard filter).
- Within that pool, cosine similarity is used on the `vector` field.
- All matches above the similarity threshold (default 70%) are stored in `linked_applications` (no limit).

---

## 4. Running the Script

### Prerequisites

- `.env` with `GEMINI_API_KEY` and `MONGODB_URI`
- MongoDB running
- Dependencies installed (`pip install -r requirements.txt`)

### Command

From project root:

```bash
python -m scripts.populate_seed_profiles
```

Or on Windows:

```powershell
cd d:\ComputerProg\Projects\Hacketon
python -m scripts.populate_seed_profiles
```

### Output

- Creates 50 users and 50 applications
- Prints progress for each profile
- Prints seed password at the end

### Re-running

- If usernames/emails already exist, the script reports duplicates and skips those users.
- To start clean, drop or clear the `users` and `clique_applications` collections before re-running.

---

## 5. Flow Diagram

```
seed_profiles.json
       │
       ▼
┌──────────────────────────────────────┐
│ For each profile:                     │
│  1. Create User (username, email)     │
│  2. Build text = goal+area+details+   │
│     third_field+city                  │
│  3. vector = Gemini.get_embedding()   │
│  4. Create CliqueApplication with     │
│     filter, vector, payload           │
└──────────────────────────────────────┘
       │
       ▼
MongoDB: users + clique_applications
       │
       ▼
New applicants submit → same text → embedding →
match against existing vectors (same goal+city)
```
