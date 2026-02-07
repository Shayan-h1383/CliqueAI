"""User model with Pydantic schema and PyMongo document class."""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr, field_validator
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from backend.config.database import db_connection


class Profile(BaseModel):
    """User profile information."""
    interests: List[str] = Field(default_factory=list, description="User interests for friendship matching")
    work_area: Optional[str] = Field(default=None, description="Work area for goal matching")
    current_goals: List[str] = Field(default_factory=list, description="Current goals for goal matching")
    struggles: List[str] = Field(default_factory=list, description="Struggles for issues matching")
    profile_pic_url: Optional[str] = Field(default=None, description="URL to profile picture")


class MatchingPreferences(BaseModel):
    """User matching preferences and focus."""
    match_type: Optional[str] = Field(default=None, description="Type of match: friendship, goal, or issues")
    current_focus_text: Optional[str] = Field(default=None, description="User's input describing their current need")
    focus_embedding: Optional[List[float]] = Field(default=None, description="Gemini embedding vector")
    last_updated: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    @field_validator('match_type')
    @classmethod
    def validate_match_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate match_type is one of the allowed values."""
        if v is not None and v not in ['friendship', 'goal', 'issues']:
            raise ValueError("match_type must be one of: friendship, goal, issues")
        return v


class UserSchema(BaseModel):
    """Pydantic schema for User validation."""
    id: Optional[str] = Field(default=None, alias="_id")
    username: str = Field(..., min_length=1, description="Unique username")
    email: EmailStr = Field(..., description="Unique email address")
    password_hash: str = Field(..., min_length=1, description="Hashed password")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    active_pod_id: Optional[str] = Field(default=None, description="Reference to active Pod")
    profile: Profile = Field(default_factory=Profile, description="User profile information")
    matching_preferences: MatchingPreferences = Field(
        default_factory=MatchingPreferences,
        description="Matching preferences and focus"
    )
    
    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class User:
    """User model for database operations."""
    
    def __init__(self):
        """Initialize User model with collection reference."""
        self.collection: Collection = db_connection.db.users
        self._create_indexes()
    
    def _create_indexes(self) -> None:
        """Create necessary indexes for the users collection."""
        try:
            self.collection.create_index("username", unique=True)
            self.collection.create_index("email", unique=True)
            self.collection.create_index("active_pod_id")
            self.collection.create_index("matching_preferences.match_type")
        except Exception as e:
            # Indexes might already exist
            pass
    
    def create(self, user_data: dict) -> str:
        """
        Create a new user.
        
        Args:
            user_data: Dictionary containing user data matching UserSchema
            
        Returns:
            str: The created user's ID as string
            
        Raises:
            ValueError: If validation fails
            DuplicateKeyError: If username or email already exists
        """
        # Validate with Pydantic
        user_schema = UserSchema(**user_data)
        
        # Convert to dict for MongoDB (excluding id if it's None)
        user_dict = user_schema.model_dump(exclude_none=True, by_alias=True)
        if '_id' in user_dict and user_dict['_id'] is None:
            del user_dict['_id']
        
        # Convert datetime to proper format
        if 'created_at' in user_dict and isinstance(user_dict['created_at'], str):
            user_dict['created_at'] = datetime.fromisoformat(user_dict['created_at'])
        
        try:
            result = self.collection.insert_one(user_dict)
            return str(result.inserted_id)
        except DuplicateKeyError as e:
            raise DuplicateKeyError(f"User with this username or email already exists: {str(e)}")
    
    def find_by_id(self, user_id: str) -> Optional[dict]:
        """
        Find user by ID.
        
        Args:
            user_id: User ID as string
            
        Returns:
            dict: User document or None if not found
        """
        try:
            user = self.collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user['_id'] = str(user['_id'])
            return user
        except Exception:
            return None
    
    def find_by_username(self, username: str) -> Optional[dict]:
        """
        Find user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            dict: User document or None if not found
        """
        user = self.collection.find_one({"username": username})
        if user:
            user['_id'] = str(user['_id'])
        return user
    
    def find_by_email(self, email: str) -> Optional[dict]:
        """
        Find user by email.
        
        Args:
            email: Email to search for
            
        Returns:
            dict: User document or None if not found
        """
        user = self.collection.find_one({"email": email})
        if user:
            user['_id'] = str(user['_id'])
        return user
    
    def update(self, user_id: str, update_data: dict) -> bool:
        """
        Update user data.
        
        Args:
            user_id: User ID as string
            update_data: Dictionary with fields to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Validate update data with Pydantic (partial)
            user_schema = UserSchema(**update_data)
            update_dict = user_schema.model_dump(exclude_none=True, by_alias=True)
            
            # Remove _id from update dict
            if '_id' in update_dict:
                del update_dict['_id']
            
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_dict}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def update_matching_preferences(
        self,
        user_id: str,
        match_type: Optional[str] = None,
        current_focus_text: Optional[str] = None,
        focus_embedding: Optional[List[float]] = None
    ) -> bool:
        """
        Update user's matching preferences.
        
        Args:
            user_id: User ID as string
            match_type: Type of match (friendship, goal, issues)
            current_focus_text: User's focus text
            focus_embedding: Embedding vector
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        update_data: dict = {
            "matching_preferences.last_updated": datetime.utcnow()
        }
        
        if match_type is not None:
            update_data["matching_preferences.match_type"] = match_type
        if current_focus_text is not None:
            update_data["matching_preferences.current_focus_text"] = current_focus_text
        if focus_embedding is not None:
            update_data["matching_preferences.focus_embedding"] = focus_embedding
        
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def set_active_pod(self, user_id: str, pod_id: Optional[str]) -> bool:
        """
        Set or clear user's active pod.
        
        Args:
            user_id: User ID as string
            pod_id: Pod ID as string, or None to clear
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            update_value = ObjectId(pod_id) if pod_id else None
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"active_pod_id": update_value}}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def find_candidates_for_matching(
        self,
        match_type: str,
        exclude_user_id: str,
        has_embedding: bool = True
    ) -> List[dict]:
        """
        Find candidate users for matching.
        
        Args:
            match_type: Type of match to filter by
            exclude_user_id: User ID to exclude from results
            has_embedding: Whether to require focus_embedding
            
        Returns:
            List[dict]: List of candidate user documents
        """
        query: dict = {
            "matching_preferences.match_type": match_type,
            "active_pod_id": None,
            "_id": {"$ne": ObjectId(exclude_user_id)}
        }
        
        if has_embedding:
            query["matching_preferences.focus_embedding"] = {"$exists": True, "$ne": None}
        
        users = list(self.collection.find(query))
        # Convert ObjectIds to strings
        for user in users:
            user['_id'] = str(user['_id'])
            if user.get('active_pod_id'):
                user['active_pod_id'] = str(user['active_pod_id'])
        
        return users

