"""Clique model: group of 2-10 users formed by mutual accepts; chat (pod) when size >= 3."""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator
from pymongo.collection import Collection

from backend.config.database import db_connection

MAX_CLIQUE_MEMBERS = 10
MIN_CLIQUE_MEMBERS = 2


class CliqueSchema(BaseModel):
    """Pydantic schema for Clique validation."""
    id: Optional[str] = Field(default=None, alias="_id")
    members: List[str] = Field(
        ...,
        min_length=MIN_CLIQUE_MEMBERS,
        max_length=MAX_CLIQUE_MEMBERS,
        description="List of user IDs (2-10)",
    )
    pod_id: Optional[str] = Field(default=None, description="Set when size >= 3 for chat")
    match_type: str = Field(default="evolve", description="evolve, enjoy, or support")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("members")
    @classmethod
    def validate_members(cls, v: List[str]) -> List[str]:
        if len(v) < MIN_CLIQUE_MEMBERS or len(v) > MAX_CLIQUE_MEMBERS:
            raise ValueError(f"members must have between {MIN_CLIQUE_MEMBERS} and {MAX_CLIQUE_MEMBERS} user IDs")
        return v

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat(),
        }


class Clique:
    """Database operations for cliques (invitation-based groups)."""

    def __init__(self):
        self.collection: Collection = db_connection.db.cliques
        self._create_indexes()

    def _create_indexes(self) -> None:
        try:
            self.collection.create_index("members")
            self.collection.create_index("pod_id")
        except Exception:
            pass

    def create(self, member_ids: List[str], match_type: str = "evolve") -> str:
        """Create a clique with exactly 2 members (called on mutual accept)."""
        member_ids = list(dict.fromkeys(member_ids))  # dedupe
        if len(member_ids) < MIN_CLIQUE_MEMBERS or len(member_ids) > MAX_CLIQUE_MEMBERS:
            raise ValueError(f"Clique must have {MIN_CLIQUE_MEMBERS}-{MAX_CLIQUE_MEMBERS} members")
        now = datetime.utcnow()
        doc = {
            "members": [ObjectId(uid) for uid in member_ids],
            "pod_id": None,
            "match_type": match_type,
            "created_at": now,
            "updated_at": now,
        }
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def find_by_id(self, clique_id: str) -> Optional[dict]:
        try:
            doc = self.collection.find_one({"_id": ObjectId(clique_id)})
            return self._normalize(doc)
        except Exception:
            return None

    def find_by_member(self, user_id: str) -> List[dict]:
        """Find all cliques that contain this user."""
        cursor = self.collection.find({"members": ObjectId(user_id)})
        return [self._normalize(d) for d in cursor if d]

    def find_containing_both(self, user_id_a: str, user_id_b: str) -> Optional[dict]:
        """Find a clique that contains both users (for merging)."""
        doc = self.collection.find_one({
            "members": {"$all": [ObjectId(user_id_a), ObjectId(user_id_b)]},
        })
        return self._normalize(doc)

    def add_member(self, clique_id: str, user_id: str) -> bool:
        """Add a member if not already in clique and under max. Returns True if added."""
        try:
            doc = self.collection.find_one({"_id": ObjectId(clique_id)})
            if not doc:
                return False
            members = [str(m) for m in doc.get("members", [])]
            if user_id in members:
                return False
            if len(members) >= MAX_CLIQUE_MEMBERS:
                return False
            result = self.collection.update_one(
                {"_id": ObjectId(clique_id)},
                {
                    "$addToSet": {"members": ObjectId(user_id)},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )
            return result.modified_count > 0
        except Exception:
            return False

    def set_pod_id(self, clique_id: str, pod_id: str) -> bool:
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(clique_id)},
                {"$set": {"pod_id": pod_id, "updated_at": datetime.utcnow()}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    def merge_into(self, target_clique_id: str, source_clique_id: str) -> bool:
        """
        Merge source clique into target: add all members from source to target
        (deduplicated, cap at MAX_CLIQUE_MEMBERS), then leave source as-is or delete.
        Returns True if merge was applied.
        """
        try:
            target = self.collection.find_one({"_id": ObjectId(target_clique_id)})
            source = self.collection.find_one({"_id": ObjectId(source_clique_id)})
            if not target or not source:
                return False
            target_members = set(str(m) for m in target.get("members", []))
            source_members = [str(m) for m in source.get("members", [])]
            to_add = [ObjectId(uid) for uid in source_members if uid not in target_members]
            if not to_add:
                return True
            new_total = len(target_members) + len(to_add)
            if new_total > MAX_CLIQUE_MEMBERS:
                to_add = to_add[: MAX_CLIQUE_MEMBERS - len(target_members)]
            result = self.collection.update_one(
                {"_id": ObjectId(target_clique_id)},
                {
                    "$addToSet": {"members": {"$each": to_add}},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )
            if result.modified_count > 0:
                self.collection.delete_one({"_id": ObjectId(source_clique_id)})
            return result.modified_count > 0
        except Exception:
            return False

    @staticmethod
    def _normalize(doc: Optional[dict]) -> Optional[dict]:
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        doc["members"] = [str(m) for m in doc.get("members", [])]
        if doc.get("pod_id"):
            doc["pod_id"] = str(doc["pod_id"])
        return doc
