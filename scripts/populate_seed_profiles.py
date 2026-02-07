"""
Seed the database with 50 user profiles and their embedding vectors.

Flow:
  1. Load seed_profiles.json
  2. For each profile:
     a. Create a User (username, email, password_hash)
     b. Build embedding text from: goal + area + details + third_field + city
     c. Get 768-dim embedding via Gemini API
     d. Create CliqueApplication with vector, payload, filter (goal+city)

All applications participate in matching (no source/non-source distinction).
Run from project root:
  python -m scripts.populate_seed_profiles

Requires: .env with GEMINI_API_KEY and MONGODB_URI
"""
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dotenv import load_dotenv

load_dotenv()


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
    from backend.config.database import db_connection
    from backend.models.user import User
    from backend.models.application import CliqueApplication
    from backend.services.gemini_service import GeminiService
    from backend.services.auth_service import AuthService

    # Ensure env
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set in .env")
        sys.exit(1)
    if not os.getenv("MONGODB_URI"):
        print("ERROR: MONGODB_URI not set in .env")
        sys.exit(1)

    # Paths
    script_dir = Path(__file__).resolve().parent
    json_path = script_dir / "seed_profiles.json"
    if not json_path.exists():
        print(f"ERROR: {json_path} not found")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    if len(profiles) != 50:
        print(f"WARNING: Expected 50 profiles, got {len(profiles)}")

    user_model = User()
    app_model = CliqueApplication()
    gemini = GeminiService()
    auth = AuthService()

    # Shared password for all seed users
    seed_password = "SeedPass123!"
    password_hash = auth.hash_password(seed_password)

    created_users = 0
    created_apps = 0
    errors = []

    for i, p in enumerate(profiles):
        username = p.get("username", f"seed_{i+1}")
        details = p.get("details", "")
        goal_text = p.get("goal", "")[:100]  # third_field, max 100
        area = p.get("area", "")
        matching_goal = p.get("matching_goal", "evolve")
        city = p.get("city", "")

        if not all([username, details, area, matching_goal, city]):
            errors.append(f"Profile {i+1} missing required fields: {username}")
            continue

        email = f"seed_{username.lower()}@example.com"

        try:
            # 1. Create user
            user_data = {
                "username": username,
                "email": email,
                "password_hash": password_hash,
            }
            user_id = user_model.create(user_data)
            created_users += 1
        except Exception as e:
            if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                # User exists - fetch by username
                existing = user_model.find_by_username(username)
                if existing:
                    user_id = existing["_id"]
                else:
                    errors.append(f"Profile {i+1} ({username}): user exists but couldn't fetch: {e}")
                    continue
            else:
                errors.append(f"Profile {i+1} ({username}): user create failed: {e}")
                continue

        # 2. Build payload (matches API schema)
        payload = {
            "goal": matching_goal,
            "area": area,
            "details": details,
            "third_field": goal_text,
            "city": city,
        }

        try:
            # 3. Get embedding
            text = _payload_to_embedding_text(payload)
            vector = gemini.get_embedding(text)
        except Exception as e:
            errors.append(f"Profile {i+1} ({username}): embedding failed: {e}")
            continue

        filter_obj = {"goal": matching_goal, "city": city.strip()}

        try:
            # 4. Create application (no source flag; all participate in matching)
            app_id = app_model.create(
                user_id=user_id,
                filter_obj=filter_obj,
                vector=vector,
                payload=payload,
            )
            created_apps += 1
            print(f"  [{i+1}/50] {username} ({matching_goal}, {city}) -> app {app_id[:8]}...")
        except Exception as e:
            errors.append(f"Profile {i+1} ({username}): application create failed: {e}")

    print()
    print("=" * 50)
    print(f"Created {created_users} users, {created_apps} applications")
    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
    print("=" * 50)
    print("Seed password for all users:", seed_password)
    print("(Users can log in with username + this password if needed)")


if __name__ == "__main__":
    main()
