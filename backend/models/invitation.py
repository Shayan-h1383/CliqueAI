"""Invitation model: clique invitations with accept/reject flow."""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator
from pymongo.collection import Collection

from backend.config.database import db_connection

INVITATION_STATUSES = ('pending', 'accepted', 'rejected')


class InvitationSchema(BaseModel):
    """Pydantic schema for Invitation validation."""
    id: Optional[str] = Field(default=None, alias="_id")
    inviter_id: str = Field(..., description="User who sent the invitation")
    invitee_id: str = Field(..., description="User who receives the invitation")
    status: str = Field(default="pending", description="pending, accepted, or rejected")
    clique_group_id: str = Field(..., description="UUID linking 2 invitations for one proposed clique")
    match_type: str = Field(..., description="evolve, enjoy, or support")
    application_id: Optional[str] = Field(default=None, description="Application this came from")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = Field(default=None, description="When invitee accepted/rejected")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in INVITATION_STATUSES:
            raise ValueError(f"status must be one of: {INVITATION_STATUSES}")
        return v

    @field_validator('match_type')
    @classmethod
    def validate_match_type(cls, v: str) -> str:
        if v not in ('evolve', 'enjoy', 'support'):
            raise ValueError("match_type must be one of: evolve, enjoy, support")
        return v

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class Invitation:
    """Database operations for clique invitations."""

    def __init__(self):
        self.collection: Collection = db_connection.db.invitations
        self._create_indexes()

    def _create_indexes(self) -> None:
        try:
            self.collection.create_index("invitee_id")
            self.collection.create_index("inviter_id")
            self.collection.create_index("status")
            self.collection.create_index("clique_group_id")
        except Exception:
            pass

    def create(
        self,
        inviter_id: str,
        invitee_id: str,
        clique_group_id: str,
        match_type: str,
        application_id: Optional[str] = None,
    ) -> str:
        """Create a single invitation."""
        doc = {
            "inviter_id": ObjectId(inviter_id),
            "invitee_id": ObjectId(invitee_id),
            "status": "pending",
            "clique_group_id": clique_group_id,
            "match_type": match_type,
            "application_id": ObjectId(application_id) if application_id else None,
            "created_at": datetime.utcnow(),
            "responded_at": None,
        }
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def find_by_id(self, invitation_id: str) -> Optional[dict]:
        try:
            doc = self.collection.find_one({"_id": ObjectId(invitation_id)})
            return self._normalize(doc)
        except Exception:
            return None

    def find_pending_by_invitee(self, invitee_id: str) -> List[dict]:
        """Find pending invitations for a user (as invitee)."""
        cursor = self.collection.find({
            "invitee_id": ObjectId(invitee_id),
            "status": "pending",
        }).sort("created_at", -1)
        return [self._normalize(d) for d in cursor if d]

    def find_pending_from_inviter_to_invitee(
        self,
        inviter_id: str,
        invitee_id: str,
        application_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Find pending invitation from inviter to invitee (so invitee can accept/reject). Scoped by application when provided."""
        query = {
            "inviter_id": ObjectId(inviter_id),
            "invitee_id": ObjectId(invitee_id),
            "status": "pending",
        }
        if application_id is not None:
            query["application_id"] = ObjectId(application_id)
        doc = self.collection.find_one(query)
        return self._normalize(doc)

    def find_any_between(
        self,
        user_id_a: str,
        user_id_b: str,
        application_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Find any invitation (any status) between two users (either direction). Scoped by application when provided."""
        oid_a, oid_b = ObjectId(user_id_a), ObjectId(user_id_b)
        query = {
            "$or": [
                {"inviter_id": oid_a, "invitee_id": oid_b},
                {"inviter_id": oid_b, "invitee_id": oid_a},
            ],
        }
        if application_id is not None:
            query["application_id"] = ObjectId(application_id)
        doc = self.collection.find_one(query)
        return self._normalize(doc)

    def find_by_clique_group_id(self, clique_group_id: str) -> List[dict]:
        """Find all invitations in a clique group."""
        cursor = self.collection.find({"clique_group_id": clique_group_id})
        return [self._normalize(d) for d in cursor if d]

    def update_status(self, invitation_id: str, status: str) -> bool:
        """Update invitation status (accepted or rejected)."""
        now = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": ObjectId(invitation_id), "status": "pending"},
            {"$set": {"status": status, "responded_at": now}}
        )
        return result.modified_count > 0

    def cancel_group(self, clique_group_id: str) -> int:
        """Cancel all pending invitations in a group (when one invitee rejects)."""
        result = self.collection.update_many(
            {"clique_group_id": clique_group_id, "status": "pending"},
            {"$set": {"status": "rejected", "responded_at": datetime.utcnow()}}
        )
        return result.modified_count

    @staticmethod
    def _normalize(doc: Optional[dict]) -> Optional[dict]:
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        doc["inviter_id"] = str(doc["inviter_id"])
        doc["invitee_id"] = str(doc["invitee_id"])
        if doc.get("application_id"):
            doc["application_id"] = str(doc["application_id"])
        return doc
