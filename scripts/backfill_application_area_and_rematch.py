"""
Backfill filter.area for existing clique applications and re-run matching.

Existing applications were created with filter = { goal, city } only. This script:
  1. Sets filter.area from payload.area for any application missing it.
  2. Re-runs matching for every application so linked_applications use the new
     goal+city+area filter (e.g. business no longer sees studies).

Run from project root:
  python -m scripts.backfill_application_area_and_rematch

Requires: .env with GEMINI_API_KEY and MONGODB_URI
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dotenv import load_dotenv

load_dotenv()


def main():
    from backend.config.database import db_connection
    from backend.models.application import CliqueApplication
    from backend.services.application_matching_service import ApplicationMatchingService

    app_model = CliqueApplication()
    coll = app_model.collection

    # 1) Backfill filter.area from payload.area where missing or empty
    cursor = coll.find({
        "$or": [
            {"filter.area": {"$exists": False}},
            {"filter.area": ""},
        ]
    })
    backfilled = 0
    for doc in cursor:
        area = (doc.get("payload") or {}).get("area") or ""
        area = str(area).strip()
        coll.update_one(
            {"_id": doc["_id"]},
            {"$set": {"filter.area": area}}
        )
        backfilled += 1
    print(f"Backfilled filter.area for {backfilled} application(s).")

    # 2) Re-run matching for every application so linked_applications are recomputed
    service = ApplicationMatchingService()
    all_docs = list(coll.find({}))
    # Normalize _id and user_id for service (find_by_id returns string ids)
    for doc in all_docs:
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
    total = len(all_docs)
    for i, app in enumerate(all_docs):
        app_id = app["_id"]
        service._run_matching(app_id, app)
        if (i + 1) % 10 == 0 or i + 1 == total:
            print(f"Re-matched {i + 1}/{total} applications.")
    print("Done. linked_applications now use goal+city+area filter.")


if __name__ == "__main__":
    main()
