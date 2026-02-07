"""Message model with Pydantic schema and PyMongo document class."""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo.collection import Collection

from backend.config.database import db_connection


class MessageSchema(BaseModel):
    """Pydantic schema for Message validation."""
    id: Optional[str] = Field(default=None, alias="_id")
    pod_id: str = Field(..., description="Reference to Pod")
    sender_id: str = Field(..., description="Reference to User who sent the message")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    read_by: List[str] = Field(default_factory=list, description="List of user IDs who have read this message")
    
    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class Message:
    """Message model for database operations."""
    
    def __init__(self):
        """Initialize Message model with collection reference."""
        self.collection: Collection = db_connection.db.messages
        self._create_indexes()
    
    def _create_indexes(self) -> None:
        """Create necessary indexes for the messages collection."""
        try:
            self.collection.create_index("pod_id")
            self.collection.create_index("timestamp")
            self.collection.create_index([("pod_id", 1), ("timestamp", 1)])
        except Exception:
            # Indexes might already exist
            pass
    
    def create(
        self,
        pod_id: str,
        sender_id: str,
        content: str
    ) -> str:
        """
        Create a new message.
        
        Args:
            pod_id: Pod ID as string
            sender_id: Sender user ID as string
            content: Message content
            
        Returns:
            str: The created message's ID as string
            
        Raises:
            ValueError: If validation fails
        """
        message_data = {
            "pod_id": ObjectId(pod_id),
            "sender_id": ObjectId(sender_id),
            "content": content,
            "timestamp": datetime.utcnow(),
            "read_by": []
        }
        
        # Validate with Pydantic
        message_schema = MessageSchema(**{
            **message_data,
            "pod_id": pod_id,
            "sender_id": sender_id
        })
        
        try:
            result = self.collection.insert_one(message_data)
            return str(result.inserted_id)
        except Exception as e:
            raise ValueError(f"Failed to create message: {str(e)}")
    
    def find_by_id(self, message_id: str) -> Optional[dict]:
        """
        Find message by ID.
        
        Args:
            message_id: Message ID as string
            
        Returns:
            dict: Message document or None if not found
        """
        try:
            message = self.collection.find_one({"_id": ObjectId(message_id)})
            if message:
                message['_id'] = str(message['_id'])
                message['pod_id'] = str(message['pod_id'])
                message['sender_id'] = str(message['sender_id'])
                message['read_by'] = [str(uid) for uid in message.get('read_by', [])]
            return message
        except Exception:
            return None
    
    def find_by_pod(
        self,
        pod_id: str,
        limit: Optional[int] = None,
        skip: int = 0
    ) -> List[dict]:
        """
        Find all messages for a pod, ordered by timestamp.
        
        Args:
            pod_id: Pod ID as string
            limit: Maximum number of messages to return
            skip: Number of messages to skip
            
        Returns:
            List[dict]: List of message documents
        """
        query = {"pod_id": ObjectId(pod_id)}
        cursor = self.collection.find(query).sort("timestamp", 1).skip(skip)
        
        if limit:
            cursor = cursor.limit(limit)
        
        messages = list(cursor)
        
        for message in messages:
            message['_id'] = str(message['_id'])
            message['pod_id'] = str(message['pod_id'])
            message['sender_id'] = str(message['sender_id'])
            message['read_by'] = [str(uid) for uid in message.get('read_by', [])]
        
        return messages
    
    def mark_as_read(self, message_id: str, user_id: str) -> bool:
        """
        Mark a message as read by a user.
        
        Args:
            message_id: Message ID as string
            user_id: User ID as string
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {
                    "_id": ObjectId(message_id),
                    "read_by": {"$ne": ObjectId(user_id)}
                },
                {
                    "$addToSet": {"read_by": ObjectId(user_id)}
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def get_unread_count(self, pod_id: str, user_id: str) -> int:
        """
        Get count of unread messages for a user in a pod.
        
        Args:
            pod_id: Pod ID as string
            user_id: User ID as string
            
        Returns:
            int: Number of unread messages
        """
        try:
            count = self.collection.count_documents({
                "pod_id": ObjectId(pod_id),
                "sender_id": {"$ne": ObjectId(user_id)},  # Don't count own messages
                "read_by": {"$ne": ObjectId(user_id)}
            })
            return count
        except Exception:
            return 0
    
    def delete_by_pod(self, pod_id: str) -> int:
        """
        Delete all messages for a pod.
        
        Args:
            pod_id: Pod ID as string
            
        Returns:
            int: Number of messages deleted
        """
        try:
            result = self.collection.delete_many({"pod_id": ObjectId(pod_id)})
            return result.deleted_count
        except Exception:
            return 0

