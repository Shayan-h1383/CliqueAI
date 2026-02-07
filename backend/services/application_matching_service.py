"""Matching service for clique applications: filter by goal+city+area, then vector similarity."""
import os
from typing import List, Dict, Optional
from backend.models.application import CliqueApplication
from backend.models.user import User
from backend.services.gemini_service import GeminiService
from backend.utils.embeddings import cosine_similarity


def _threshold() -> float:
    """Similarity threshold (default 51%); override with env SIMILARITY_THRESHOLD."""
    return float(os.getenv("SIMILARITY_THRESHOLD", "0.51"))


def _payload_to_embedding_text(payload: dict) -> str:
    """Build text for embedding: goal, area, details, third_field, city (area in embedding, not filter)."""
    parts = [
        payload.get("goal", ""),
        payload.get("area", ""),
        payload.get("details", ""),
        payload.get("third_field", ""),
        payload.get("city", ""),
    ]
    return " ".join(str(p).strip() for p in parts if p)


class ApplicationMatchingService:
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        self.gemini = gemini_service or GeminiService()
        self.app_model = CliqueApplication()
        self.user_model = User()

    def submit_and_match(
        self,
        user_id: str,
        goal: str,
        area: str,
        details: str,
        third_field: str,
        city: str,
    ) -> dict:
        """
        Create application, get embedding (area in text), run matching (filter = goal + city + area).
        Returns created application with linked_applications (all matches above threshold, no limit).
        """
        payload = {
            "goal": goal,
            "area": area,
            "details": details,
            "third_field": third_field,
            "city": city,
        }
        area_stripped = area.strip()
        filter_obj = {"goal": goal, "city": city.strip(), "area": area_stripped}
        text = _payload_to_embedding_text(payload)
        vector = self.gemini.get_embedding(text)
        app_id = self.app_model.create(
            user_id=user_id,
            filter_obj=filter_obj,
            vector=vector,
            payload=payload,
        )
        application = self.app_model.find_by_id(app_id)
        self._run_matching(app_id, application)
        return self.app_model.find_by_id(app_id)

    def _run_matching(self, application_id: str, application: Optional[dict] = None) -> None:
        """Run matching: same goal+city+area, all above threshold, no limit."""
        if application is None:
            application = self.app_model.find_by_id(application_id)
        if not application:
            return
        goal = application["filter"]["goal"]
        city = application["filter"]["city"]
        area = application["filter"].get("area") or application.get("payload", {}).get("area", "")
        if not area:
            self.app_model.update_linked_applications(application_id, [])
            return
        vector = application["vector"]
        payload = application["payload"]
        threshold = _threshold()

        candidates = self.app_model.find_by_filter(
            goal, city, area, application_id, exclude_user_id=application.get("user_id")
        )
        if not candidates:
            self.app_model.update_linked_applications(application_id, [])
            return

        scored = []
        for c in candidates:
            try:
                sim = cosine_similarity(vector, c["vector"])
                scored.append((sim, c))
            except Exception:
                continue
        scored.sort(key=lambda x: x[0], reverse=True)
        above = [(s, c) for s, c in scored if s >= threshold]

        if not above:
            self.app_model.update_linked_applications(application_id, [])
            return

        linked_payloads_with_scores = [{"payload": c["payload"], "similarity_score": s} for s, c in above]
        why_list = self.gemini.generate_similarity_reports(payload, linked_payloads_with_scores, goal)

        linked_entries = []
        for i, (score, cand) in enumerate(above):
            why = why_list[i] if i < len(why_list) else "Good match based on your profile."
            linked_entries.append({
                "application_id": cand["_id"],
                "similarity_score": round(score, 4),
                "why_selected": why,
            })
        self.app_model.update_linked_applications(application_id, linked_entries)

        # Bidirectional: ensure each linked application also has this app in their list
        # (skip if other application is from the same user - never suggest self to self)
        my_user_id = application.get("user_id")
        for entry in linked_entries:
            other_app_id = entry["application_id"]
            other_app = self.app_model.find_by_id(other_app_id)
            if not other_app or str(other_app.get("user_id")) == str(my_user_id):
                continue
            existing = other_app.get("linked_applications") or []
            if any(str(e.get("application_id")) == str(application_id) for e in existing):
                continue
            new_entry = {
                "application_id": application_id,
                "similarity_score": entry["similarity_score"],
                "why_selected": "Good match based on your profile.",
            }
            self.app_model.append_linked_application(other_app_id, new_entry)
