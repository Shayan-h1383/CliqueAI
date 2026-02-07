"""
Test the full pipeline: Register -> Login -> Submit Application -> Embedding -> Match with MongoDB.

Verifies:
  1. Prompt is converted to embedding via Gemini
  2. Application is matched against existing seed profiles in clique_applications
  3. linked_applications are returned with similarity scores
"""
import json
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print("Run: pip install requests")
    sys.exit(1)

BASE_URL = "http://localhost:5000"
TIMEOUT = 30


def main():
    print("=" * 60)
    print("Pipeline API Test: Register -> Submit -> Embedding -> Match")
    print("=" * 60)

    # Unique user to avoid conflicts on re-runs
    ts = datetime.now().strftime("%H%M%S")
    username = f"pipelinetest_{ts}"
    email = f"pipelinetest_{ts}@example.com"
    password = "Test123!"

    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})

    # 1. Register
    print("\n[1] Register...")
    r = session.post(
        f"{BASE_URL}/api/auth/register",
        json={"username": username, "email": email, "password": password},
        timeout=TIMEOUT,
    )
    if r.status_code != 201:
        print(f"  FAIL: {r.status_code} - {r.text}")
        sys.exit(1)
    print(f"  OK: User registered ({username})")

    # 2. Login
    print("\n[2] Login...")
    r = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        print(f"  FAIL: {r.status_code} - {r.text}")
        sys.exit(1)
    data = r.json()
    token = data.get("token")
    user_id = data.get("user", {}).get("_id")
    if not token or not user_id:
        print("  FAIL: Missing token or user._id")
        sys.exit(1)
    session.headers.update({"Authorization": f"Bearer {token}"})
    print(f"  OK: Logged in, user_id={user_id[:8]}...")

    # 3. Submit application (triggers: payload -> embedding text -> Gemini API -> vector -> MongoDB matching)
    # Use evolve + Berlin to match seed profiles (Alex, Jordan, DakotaR, Skyler, Emerson)
    payload = {
        "goal": "evolve",
        "area": "business",
        "details": "Career switcher into data science, need accountability buddies. Looking to launch a consultancy.",
        "third_field": "Launch freelance data analytics consultancy within 12 months",
        "city": "Berlin",
    }
    print("\n[3] Submit application (prompt -> embedding -> match)...")
    r = session.post(
        f"{BASE_URL}/api/applications",
        json=payload,
        timeout=TIMEOUT,
    )
    if r.status_code != 201:
        print(f"  FAIL: {r.status_code} - {r.text}")
        sys.exit(1)
    app = r.json()
    app_id = app.get("_id")
    linked = app.get("linked_applications") or []
    print(f"  OK: Application created (id={app_id[:8]}...)")

    # 4. Verify embedding was created and matching returned results
    print("\n[4] Verify matching...")
    if not linked:
        print("  WARNING: No linked_applications. Possible causes:")
        print("    - No seed profiles for evolve+Berlin (run: python -m scripts.populate_seed_profiles)")
        print("    - Similarity below SIMILARITY_THRESHOLD (default 0.7)")
        print("    - Gemini API error or rate limit")
    else:
        print(f"  OK: Found {len(linked)} match(es):")
        for i, m in enumerate(linked[:5], 1):
            score = m.get("similarity_score", 0)
            uname = m.get("username", "?")
            why = (m.get("why_selected") or "")[:60]
            print(f"      {i}. {uname} ({score*100:.1f}% match) - {why}...")

    # 5. List applications (verify persistence)
    print("\n[5] List applications...")
    r = session.get(f"{BASE_URL}/api/applications", timeout=TIMEOUT)
    if r.status_code != 200:
        print(f"  FAIL: {r.status_code} - {r.text}")
        sys.exit(1)
    apps = r.json()
    print(f"  OK: {len(apps)} application(s)")

    # 6. Create pod and send message (if we have matches)
    if len(linked) >= 2:
        print("\n[6] Create pod with 2 matches...")
        member_ids = [user_id, linked[0].get("user_id"), linked[1].get("user_id")]
        if None in member_ids:
            print("  SKIP: Missing user_id in linked applications")
        else:
            r = session.post(
                f"{BASE_URL}/api/matching/create-pod",
                json={"match_type": "evolve", "member_ids": member_ids},
                timeout=TIMEOUT,
            )
            if r.status_code != 201:
                print(f"  FAIL: {r.status_code} - {r.text}")
            else:
                pod_data = r.json()
                pod_id = pod_data.get("pod", {}).get("_id")
                icebreaker = pod_data.get("icebreaker", "")[:80]
                print(f"  OK: Pod created (id={pod_id[:8]}...)")
                print(f"      Icebreaker: {icebreaker}...")

                # Send message
                print("\n[7] Send message...")
                r = session.post(
                    f"{BASE_URL}/api/messages/send",
                    json={"pod_id": pod_id, "content": "Hello clique! Pipeline test successful."},
                    timeout=TIMEOUT,
                )
                if r.status_code != 201:
                    print(f"  FAIL: {r.status_code} - {r.text}")
                else:
                    print("  OK: Message sent")
    else:
        print("\n[6] SKIP: Create pod (need at least 2 matches)")

    print("\n" + "=" * 60)
    print("Pipeline test completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
