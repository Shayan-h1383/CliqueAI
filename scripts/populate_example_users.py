"""
Populate the database with example users and their clique applications.

Creates users + CliqueApplication records (with embeddings) so you have
matchable data. Add more entries in EXAMPLE_APPLICATIONS below.

Flow:
  1. For each entry in EXAMPLE_APPLICATIONS:
     a. Create a User (username, email, password_hash)
     b. Build payload: goal, area, details, third_field, city
     c. Get 768-dim embedding via Gemini API
     d. Create CliqueApplication with vector, payload, filter (goal + city + area)

Run from project root:
  python -m scripts.populate_example_users

Requires: .env with GEMINI_API_KEY and MONGODB_URI
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# ADD YOUR DATA HERE
# =============================================================================
# Copy a block below and fill in the fields to add more users with applications.
# Required: username, goal, area, details, third_field, city
# - goal: one of "evolve", "enjoy", "support"
# - area: e.g. "business", "studies", "arts development", "sports"
# - details: longer description (used for matching)
# - third_field: short summary / one-liner goal (max ~100 chars)
# - city: for same-city matching
#
EXAMPLE_APPLICATIONS = [
    {
        "username": "Parker",
        "goal": "evolve",
        "area": "business",
        "details": "MBA graduate exploring entrepreneurship. Has ideas but paralyzed by analysis. Wants a small group to bounce ideas off and keep momentum. Based in Stuttgart.",
        "third_field": "Validate one business idea and get first paying customer",
        "city": "Stuttgart",
    },
    {
        "username": "Jordan",
        "goal": "evolve",
        "area": "studies",
        "details": "University student studying computer science, struggling with algorithms and competitive programming. Want to build a side project but overwhelmed by coursework. Need peers who can explain concepts simply and share study techniques.",
        "third_field": "Master DSA and land an internship by summer",
        "city": "Berlin",
    },
    # -------------------------------------------------------------------------
    # ADD MORE APPLICATIONS BELOW (copy a block above and edit)
    # -------------------------------------------------------------------------
    # {
    #     "username": "YourUsername",
    #     "goal": "evolve",           # or "enjoy" or "support"
    #     "area": "business",         # e.g. business, studies, arts development
    #     "details": "Your longer description for matching...",
    #     "third_field": "One-line summary of your goal",
    #     "city": "YourCity",
    # },
]


def _payload_to_embedding_text(payload: dict) -> str:
    """Build text for embedding - must match application_matching_service._payload_to_embedding_text."""
    parts = [
        payload.get("goal", ""),
        payload.get("area", ""),
        payload.get("details", ""),
        payload.get("third_field", ""),
        payload.get("city", ""),
    ]
    return " ".join(str(p).strip() for p in parts if p)


def main():
    from backend.models.user import User
    from backend.models.application import CliqueApplication
    from backend.services.gemini_service import GeminiService
    from backend.services.auth_service import AuthService

    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set in .env")
        sys.exit(1)
    if not os.getenv("MONGODB_URI"):
        print("ERROR: MONGODB_URI not set in .env")
        sys.exit(1)

    # Filter out commented/placeholder entries (dicts with no username or empty)
    entries = [
        e for e in EXAMPLE_APPLICATIONS
        if isinstance(e, dict) and e.get("username") and e.get("goal") and e.get("city")
    ]
    if not entries:
        print("ERROR: No valid entries in EXAMPLE_APPLICATIONS. Add at least one user (see comments in script).")
        sys.exit(1)

    user_model = User()
    app_model = CliqueApplication()
    gemini = GeminiService()
    auth = AuthService()

    seed_password = "ExamplePass123!"
    password_hash = auth.hash_password(seed_password)

    created_users = 0
    created_apps = 0
    errors = []

    for i, p in enumerate(entries):
        username = p["username"].strip()
        goal = p["goal"].strip().lower()
        area = p["area"].strip()
        details = p.get("details", "").strip()
        third_field = (p.get("third_field") or "")[:100]
        city = p["city"].strip()

        if goal not in ("evolve", "enjoy", "support"):
            errors.append(f"{username}: goal must be evolve, enjoy, or support (got '{goal}')")
            continue

        email = f"{username.lower()}@example.com"

        try:
            user_data = {
                "username": username,
                "email": email,
                "password_hash": password_hash,
            }
            user_id = user_model.create(user_data)
            created_users += 1
        except Exception as e:
            if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                existing = user_model.find_by_username(username)
                if existing:
                    user_id = existing["_id"]
                else:
                    errors.append(f"{username}: user exists but couldn't fetch: {e}")
                    continue
            else:
                errors.append(f"{username}: user create failed: {e}")
                continue

        payload = {
            "goal": goal,
            "area": area,
            "details": details,
            "third_field": third_field,
            "city": city,
        }

        try:
            text = _payload_to_embedding_text(payload)
            vector = gemini.get_embedding(text)
        except Exception as e:
            errors.append(f"{username}: embedding failed: {e}")
            continue

        # Filter must include goal, city, and area for matching
        filter_obj = {"goal": goal, "city": city, "area": area}

        try:
            app_id = app_model.create(
                user_id=user_id,
                filter_obj=filter_obj,
                vector=vector,
                payload=payload,
            )
            created_apps += 1
            print(f"  [{i+1}] {username} ({goal}, {city}) -> app {app_id[:8]}...")
        except Exception as e:
            errors.append(f"{username}: application create failed: {e}")

    print()
    print("=" * 50)
    print(f"Created {created_users} users, {created_apps} applications")
    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
    print("=" * 50)
    print("Login password for all example users:", seed_password)


if __name__ == "__main__":
    main()
