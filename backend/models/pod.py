"""Pod model with Pydantic schema and PyMongo document class."""
from datetime import datetime, timedelta
from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator
from pymongo.collection import Collection

from backend.config.database import db_connection


MAX_POD_MEMBERS = 10


class PodSchema(BaseModel):
    """Pydantic schema for Pod validation."""
    id: Optional[str] = Field(default=None, alias="_id")
    pod_type: str = Field(..., description="Type of pod: evolve, enjoy, or support")
    members: List[str] = Field(..., min_length=1, max_length=MAX_POD_MEMBERS, description="List of user IDs (max 10)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Pod creation timestamp")
    expires_at: datetime = Field(..., description="Pod expiration timestamp (48 hours from creation)")
    is_active: bool = Field(default=True, description="Whether the pod is currently active")
    gemini_icebreaker: Optional[str] = Field(default=None, description="Generated explanation of why matched")
    focus_context: Optional[str] = Field(default=None, description="Aggregated context from all members")
    
    @field_validator('pod_type')
    @classmethod
    def validate_pod_type(cls, v: str) -> str:
        """Validate pod_type is one of the allowed values."""
        if v not in ['evolve', 'enjoy', 'support']:
            raise ValueError("pod_type must be one of: evolve, enjoy, support")
        return v
    
    @field_validator('members')
    @classmethod
    def validate_members(cls, v: List[str]) -> List[str]:
        """Validate members list length."""
        if len(v) < 1 or len(v) > MAX_POD_MEMBERS:
            raise ValueError(f"members must contain between 1 and {MAX_POD_MEMBERS} user IDs")
        return v
    
    @field_validator('expires_at')
    @classmethod
    def validate_expires_at(cls, v: datetime, info) -> datetime:
        """Validate expires_at is 48 hours from created_at."""
        created_at = info.data.get('created_at', datetime.utcnow())
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        expected_expiry = created_at + timedelta(hours=48)
        # Allow small tolerance for timing differences
        if abs((v - expected_expiry).total_seconds()) > 60:
            # If not set correctly, set it to 48 hours from created_at
            return created_at + timedelta(hours=48)
        return v
    
    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class Pod:
    """Pod model for database operations."""
    
    def __init__(self):
        """Initialize Pod model with collection reference."""
        self.collection: Collection = db_connection.db.pods
        self._create_indexes()
    
    def _create_indexes(self) -> None:
        """Create necessary indexes for the pods collection."""
        try:
            self.collection.create_index("is_active")
            self.collection.create_index("expires_at")
            self.collection.create_index("pod_type")
        except Exception:
            # Indexes might already exist
            pass
    
    def create(
        self,
        pod_type: str,
        member_ids: List[str],
        gemini_icebreaker: Optional[str] = None,
        focus_context: Optional[str] = None
    ) -> str:
        """
        Create a new pod.
        
        Args:
            pod_type: Type of pod (evolve, enjoy, support)
            member_ids: List of user IDs (max 3)
            gemini_icebreaker: Generated icebreaker text
            focus_context: Aggregated context from members
            
        Returns:
            str: The created pod's ID as string
            
        Raises:
            ValueError: If validation fails
        """
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(hours=48)
        
        pod_data = {
            "pod_type": pod_type,
            "members": [ObjectId(mid) for mid in member_ids],
            "created_at": created_at,
            "expires_at": expires_at,
            "is_active": True,
            "gemini_icebreaker": gemini_icebreaker,
            "focus_context": focus_context
        }
        
        # Validate with Pydantic
        pod_schema = PodSchema(**{
            **pod_data,
            "members": member_ids  # Pass as strings for validation
        })
        
        try:
            result = self.collection.insert_one(pod_data)
            return str(result.inserted_id)
        except Exception as e:
            raise ValueError(f"Failed to create pod: {str(e)}")
    
    def find_by_id(self, pod_id: str) -> Optional[dict]:
        """
        Find pod by ID.
        
        Args:
            pod_id: Pod ID as string
            
        Returns:
            dict: Pod document or None if not found
        """
        try:
            pod = self.collection.find_one({"_id": ObjectId(pod_id)})
            if pod:
                pod['_id'] = str(pod['_id'])
                pod['members'] = [str(mid) for mid in pod.get('members', [])]
            return pod
        except Exception:
            return None
    
    def find_active_by_user(self, user_id: str) -> Optional[dict]:
        """
        Find active pod for a user.
        
        Args:
            user_id: User ID as string
            
        Returns:
            dict: Active pod document or None if not found
        """
        try:
            pod = self.collection.find_one({
                "members": ObjectId(user_id),
                "is_active": True,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            if pod:
                pod['_id'] = str(pod['_id'])
                pod['members'] = [str(mid) for mid in pod.get('members', [])]
            return pod
        except Exception:
            return None
    
    def update(self, pod_id: str, update_data: dict) -> bool:
        """
        Update pod data.
        
        Args:
            pod_id: Pod ID as string
            update_data: Dictionary with fields to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Convert member IDs to ObjectIds if present
            if 'members' in update_data:
                update_data['members'] = [ObjectId(mid) for mid in update_data['members']]
            
            result = self.collection.update_one(
                {"_id": ObjectId(pod_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def deactivate(self, pod_id: str) -> bool:
        """
        Deactivate a pod.
        
        Args:
            pod_id: Pod ID as string
            
        Returns:
            bool: True if deactivation was successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(pod_id)},
                {"$set": {"is_active": False}}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def deactivate_expired(self) -> int:
        """
        Deactivate all expired pods.
        
        Returns:
            int: Number of pods deactivated
        """
        try:
            result = self.collection.update_many(
                {
                    "expires_at": {"$lt": datetime.utcnow()},
                    "is_active": True
                },
                {"$set": {"is_active": False}}
            )
            return result.modified_count
        except Exception:
            return 0
    
    def find_all_active(self) -> List[dict]:
        """
        Find all active pods.
        
        Returns:
            List[dict]: List of active pod documents
        """
        pods = list(self.collection.find({
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        }))
        
        for pod in pods:
            pod['_id'] = str(pod['_id'])
            pod['members'] = [str(mid) for mid in pod.get('members', [])]
        
        return pods

    def find_active_by_member(self, user_id: str) -> List[dict]:
        """
        Find all active pods where the user is a member.
        """
        pods = list(self.collection.find({
            "members": ObjectId(user_id),
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        }).sort("created_at", -1))
        
        for pod in pods:
            pod['_id'] = str(pod['_id'])
            pod['members'] = [str(mid) for mid in pod.get('members', [])]
        
        return pods

    def add_member(self, pod_id: str, user_id: str) -> bool:
        """Add a member to an existing pod if under max. Returns True if added."""
        try:
            pod = self.collection.find_one({"_id": ObjectId(pod_id)})
            if not pod:
                return False
            members = list(pod.get("members", []))
            if ObjectId(user_id) in members:
                return False
            if len(members) >= MAX_POD_MEMBERS:
                return False
            result = self.collection.update_one(
                {"_id": ObjectId(pod_id)},
                {"$addToSet": {"members": ObjectId(user_id)}}
            )
            return result.modified_count > 0
        except Exception:
            return False

