"""Clique Application model: one submission per goal (evolve/enjoy/support) with filter and vector."""
import re
from datetime import datetime
from typing import Optional, List, Any
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator
from pymongo.collection import Collection

from backend.config.database import db_connection

GOALS = ('evolve', 'enjoy', 'support')
APPLICATION_STATUSES = ('pending', 'matched', 'rejected')


class ApplicationFilter(BaseModel):
    """Hard filter for matching: goal + city + area."""
    goal: str = Field(..., description="evolve, enjoy, or support")
    city: str = Field(..., min_length=1, description="City (same-city matching)")
    area: str = Field(..., min_length=1, description="Area (e.g. business, studies)")

    @field_validator('goal')
    @classmethod
    def validate_goal(cls, v: str) -> str:
        if v not in GOALS:
            raise ValueError(f"goal must be one of: {GOALS}")
        return v


class LinkedApplication(BaseModel):
    """One linked suggestion with score and why-selected text."""
    application_id: str = Field(..., description="Linked application _id")
    similarity_score: float = Field(..., ge=0, le=1)
    why_selected: Optional[str] = Field(default=None, description="Why this person was selected for you")


class CliqueApplicationSchema(BaseModel):
    """Pydantic schema for Clique Application."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str = Field(..., description="Applicant user ID")
    status: str = Field(default="pending", description="pending, matched, or rejected")
    filter: ApplicationFilter = Field(..., description="Hard filter: goal + city + area")
    vector: List[float] = Field(..., min_length=768, max_length=768, description="768-dim embedding")
    payload: dict = Field(default_factory=dict, description="Form data: goal, area, details, third_field, city")
    linked_applications: List[dict] = Field(default_factory=list, description="[{ application_id, similarity_score, why_selected }]")
    date_submitted: datetime = Field(default_factory=datetime.utcnow)
    date_match_found: Optional[datetime] = Field(default=None)
    rejected_at: Optional[datetime] = Field(default=None)
    rejected_reason: Optional[str] = Field(default=None)

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in APPLICATION_STATUSES:
            raise ValueError(f"status must be one of: {APPLICATION_STATUSES}")
        return v

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class CliqueApplication:
    """Database operations for clique applications."""

    def __init__(self):
        self.collection: Collection = db_connection.db.clique_applications
        self._create_indexes()

    def _create_indexes(self) -> None:
        try:
            self.collection.create_index("user_id")
            self.collection.create_index("status")
            self.collection.create_index("date_submitted")
            self.collection.create_index([
                ("filter.goal", 1),
                ("filter.city", 1),
                ("filter.area", 1),
            ])
        except Exception:
            pass

    def create(
        self,
        user_id: str,
        filter_obj: dict,
        vector: List[float],
        payload: dict,
    ) -> str:
        """Create application with status pending."""
        now = datetime.utcnow()
        doc = {
            "user_id": ObjectId(user_id),
            "status": "pending",
            "filter": filter_obj,
            "vector": vector,
            "payload": payload,
            "linked_applications": [],
            "date_submitted": now,
            "date_match_found": None,
            "rejected_at": None,
            "rejected_reason": None,
        }
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def find_by_id(self, application_id: str) -> Optional[dict]:
        try:
            doc = self.collection.find_one({"_id": ObjectId(application_id)})
            return self._normalize(doc)
        except Exception:
            return None

    def find_by_user_id(self, user_id: str) -> List[dict]:
        cursor = self.collection.find({"user_id": ObjectId(user_id)}).sort("date_submitted", -1)
        return [self._normalize(d) for d in cursor if d]

    def find_by_filter(
        self,
        goal: str,
        city: str,
        area: str,
        exclude_application_id: str,
        exclude_user_id: Optional[str] = None,
    ) -> List[dict]:
        """Find ALL applications with same goal, city, and area (hard filter). City and area match case-insensitively. Excludes given app, same user, and rejected."""
        query = {
            "filter.goal": goal,
            "filter.city": {"$regex": f"^{re.escape(city.strip())}$", "$options": "i"},
            "filter.area": {"$regex": f"^{re.escape(area.strip())}$", "$options": "i"},
            "status": {"$in": ["pending", "matched"]},
            "_id": {"$ne": ObjectId(exclude_application_id)},
        }
        if exclude_user_id:
            query["user_id"] = {"$ne": ObjectId(exclude_user_id)}
        cursor = self.collection.find(query)
        return [self._normalize(d) for d in cursor if d]

    def update_linked_applications(self, application_id: str, linked: List[dict]) -> bool:
        now = datetime.utcnow()
        status = "matched" if linked else "pending"
        set_fields = {
            "linked_applications": linked,
            "date_match_found": now if linked else None,
            "status": status,
        }
        result = self.collection.update_one(
            {"_id": ObjectId(application_id)},
            {"$set": set_fields}
        )
        return result.modified_count > 0

    def append_linked_application(self, application_id: str, entry: dict) -> bool:
        """Add a single linked application if not already present (for bidirectional suggestions)."""
        app_id_str = str(application_id)
        other_id = entry.get("application_id") or entry.get("_id")
        if not other_id:
            return False
        other_id_str = str(other_id)
        doc = self.collection.find_one({"_id": ObjectId(application_id)})
        if not doc:
            return False
        existing = doc.get("linked_applications") or []
        if any(str(e.get("application_id")) == other_id_str for e in existing):
            return False
        new_list = existing + [entry]
        now = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": ObjectId(application_id)},
            {
                "$set": {
                    "linked_applications": new_list,
                    "date_match_found": now,
                    "status": "matched",
                }
            },
        )
        return result.modified_count > 0

    def update_status(self, application_id: str, status: str, **kwargs) -> bool:
        set_fields = {"status": status, **kwargs}
        if status == "rejected":
            set_fields["rejected_at"] = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": ObjectId(application_id)},
            {"$set": set_fields}
        )
        return result.modified_count > 0

    @staticmethod
    def _normalize(doc: Optional[dict]) -> Optional[dict]:
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        return doc
