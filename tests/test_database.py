"""Tests for database connection and CRUD operations."""
import pytest
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pymongo.errors import ConnectionFailure, DuplicateKeyError

from backend.config.database import DatabaseConnection, db_connection
from backend.models.user import User, UserSchema
from backend.models.pod import Pod, PodSchema
from backend.models.message import Message, MessageSchema


class TestDatabaseConnection:
    """Tests for database connection."""
    
    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://localhost:27017/test'})
    @patch('backend.config.database.MongoClient')
    def test_connection_success(self, mock_mongo_client):
        """Test successful database connection."""
        mock_client = MagicMock()
        mock_client.admin.command.return_value = True
        mock_client.__getitem__.return_value = MagicMock()
        mock_mongo_client.return_value = mock_client
        
        # Reset singleton
        DatabaseConnection._instance = None
        DatabaseConnection._client = None
        DatabaseConnection._db = None
        
        conn = DatabaseConnection()
        
        assert conn.client is not None
        assert conn.db is not None
        mock_client.admin.command.assert_called_once_with('ping')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_connection_missing_uri(self):
        """Test that missing MONGODB_URI raises ConfigurationError."""
        # Reset singleton
        DatabaseConnection._instance = None
        DatabaseConnection._client = None
        DatabaseConnection._db = None
        
        conn = DatabaseConnection()
        with pytest.raises(Exception):  # ConfigurationError - triggered on first access
            _ = conn.client
    
    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://localhost:27017/test'})
    @patch('backend.config.database.MongoClient')
    def test_connection_failure(self, mock_mongo_client):
        """Test handling of connection failure."""
        mock_mongo_client.side_effect = ConnectionFailure("Connection failed")
        
        # Reset singleton
        DatabaseConnection._instance = None
        DatabaseConnection._client = None
        DatabaseConnection._db = None
        
        conn = DatabaseConnection()
        with pytest.raises(ConnectionFailure):
            _ = conn.client
    
    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://localhost:27017/test'})
    @patch('backend.config.database.MongoClient')
    def test_health_check(self, mock_mongo_client):
        """Test health check method."""
        mock_client = MagicMock()
        mock_client.admin.command.return_value = True
        mock_client.__getitem__.return_value = MagicMock()
        mock_mongo_client.return_value = mock_client
        
        # Reset singleton
        DatabaseConnection._instance = None
        DatabaseConnection._client = None
        DatabaseConnection._db = None
        
        conn = DatabaseConnection()
        assert conn.health_check() is True
        
        # Test failure case
        mock_client.admin.command.side_effect = Exception("Connection lost")
        assert conn.health_check() is False
    
    @patch.dict(os.environ, {'MONGODB_URI': 'mongodb://localhost:27017/test'})
    @patch('backend.config.database.MongoClient')
    def test_singleton_pattern(self, mock_mongo_client):
        """Test that DatabaseConnection is a singleton."""
        mock_client = MagicMock()
        mock_client.admin.command.return_value = True
        mock_client.__getitem__.return_value = MagicMock()
        mock_mongo_client.return_value = mock_client
        
        # Reset singleton
        DatabaseConnection._instance = None
        DatabaseConnection._client = None
        DatabaseConnection._db = None
        
        conn1 = DatabaseConnection()
        conn2 = DatabaseConnection()
        
        assert conn1 is conn2


class TestUserModel:
    """Tests for User model CRUD operations."""
    
    @pytest.fixture
    def mock_collection(self):
        """Create a mock collection for User model."""
        with patch('backend.models.user.db_connection') as mock_db:
            mock_collection = MagicMock()
            mock_db.db.users = mock_collection
            user = User()
            yield mock_collection, user
    
    def test_create_user(self, mock_collection):
        """Test creating a user."""
        mock_col, user_model = mock_collection
        
        mock_col.insert_one.return_value.inserted_id = "507f1f77bcf86cd799439011"
        
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashed_password"
        }
        
        user_id = user_model.create(user_data)
        
        assert user_id == "507f1f77bcf86cd799439011"
        mock_col.insert_one.assert_called_once()
    
    def test_create_user_duplicate(self, mock_collection):
        """Test creating a user with duplicate username/email."""
        mock_col, user_model = mock_collection
        
        mock_col.insert_one.side_effect = DuplicateKeyError("Duplicate key")
        
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashed_password"
        }
        
        with pytest.raises(DuplicateKeyError):
            user_model.create(user_data)
    
    def test_find_by_id(self, mock_collection):
        """Test finding user by ID."""
        mock_col, user_model = mock_collection
        
        from bson import ObjectId
        test_id = ObjectId()
        mock_col.find_one.return_value = {
            "_id": test_id,
            "username": "testuser",
            "email": "test@example.com"
        }
        
        result = user_model.find_by_id(str(test_id))
        
        assert result is not None
        assert result["_id"] == str(test_id)
        mock_col.find_one.assert_called_once()
    
    def test_find_by_username(self, mock_collection):
        """Test finding user by username."""
        mock_col, user_model = mock_collection
        
        from bson import ObjectId
        test_id = ObjectId()
        mock_col.find_one.return_value = {
            "_id": test_id,
            "username": "testuser",
            "email": "test@example.com"
        }
        
        result = user_model.find_by_username("testuser")
        
        assert result is not None
        assert result["username"] == "testuser"
    
    def test_update_matching_preferences(self, mock_collection):
        """Test updating matching preferences."""
        mock_col, user_model = mock_collection
        
        from bson import ObjectId
        test_id = ObjectId()
        mock_col.update_one.return_value.modified_count = 1
        
        embedding = [0.1] * 768
        result = user_model.update_matching_preferences(
            str(test_id),
            match_type="friendship",
            current_focus_text="Looking for friends",
            focus_embedding=embedding
        )
        
        assert result is True
        mock_col.update_one.assert_called_once()
    
    def test_find_candidates_for_matching(self, mock_collection):
        """Test finding candidates for matching."""
        mock_col, user_model = mock_collection
        
        from bson import ObjectId
        test_id1 = ObjectId()
        test_id2 = ObjectId()
        
        mock_col.find.return_value = [
            {
                "_id": test_id1,
                "username": "user1",
                "matching_preferences": {
                    "match_type": "friendship",
                    "focus_embedding": [0.1] * 768
                }
            },
            {
                "_id": test_id2,
                "username": "user2",
                "matching_preferences": {
                    "match_type": "friendship",
                    "focus_embedding": [0.2] * 768
                }
            }
        ]
        
        candidates = user_model.find_candidates_for_matching(
            match_type="friendship",
            exclude_user_id=str(ObjectId()),
            has_embedding=True
        )
        
        assert len(candidates) == 2
        assert all("_id" in c for c in candidates)


class TestPodModel:
    """Tests for Pod model CRUD operations."""
    
    @pytest.fixture
    def mock_collection(self):
        """Create a mock collection for Pod model."""
        with patch('backend.models.pod.db_connection') as mock_db:
            mock_collection = MagicMock()
            mock_db.db.pods = mock_collection
            pod = Pod()
            yield mock_collection, pod
    
    def test_create_pod(self, mock_collection):
        """Test creating a pod."""
        mock_col, pod_model = mock_collection
        
        from bson import ObjectId
        test_id = ObjectId()
        mock_col.insert_one.return_value.inserted_id = test_id
        
        pod_id = pod_model.create(
            pod_type="friendship",
            member_ids=[str(ObjectId()), str(ObjectId()), str(ObjectId())]
        )
        
        assert pod_id == str(test_id)
        mock_col.insert_one.assert_called_once()
    
    def test_find_by_id(self, mock_collection):
        """Test finding pod by ID."""
        mock_col, pod_model = mock_collection
        
        from bson import ObjectId
        test_id = ObjectId()
        member_id = ObjectId()
        mock_col.find_one.return_value = {
            "_id": test_id,
            "pod_type": "friendship",
            "members": [member_id],
            "is_active": True
        }
        
        result = pod_model.find_by_id(str(test_id))
        
        assert result is not None
        assert result["_id"] == str(test_id)
        assert result["members"] == [str(member_id)]
    
    def test_deactivate_pod(self, mock_collection):
        """Test deactivating a pod."""
        mock_col, pod_model = mock_collection
        
        from bson import ObjectId
        test_id = ObjectId()
        mock_col.update_one.return_value.modified_count = 1
        
        result = pod_model.deactivate(str(test_id))
        
        assert result is True
        mock_col.update_one.assert_called_once()


class TestMessageModel:
    """Tests for Message model CRUD operations."""
    
    @pytest.fixture
    def mock_collection(self):
        """Create a mock collection for Message model."""
        with patch('backend.models.message.db_connection') as mock_db:
            mock_collection = MagicMock()
            mock_db.db.messages = mock_collection
            message = Message()
            yield mock_collection, message
    
    def test_create_message(self, mock_collection):
        """Test creating a message."""
        mock_col, message_model = mock_collection
        
        from bson import ObjectId
        test_id = ObjectId()
        mock_col.insert_one.return_value.inserted_id = test_id
        
        message_id = message_model.create(
            pod_id=str(ObjectId()),
            sender_id=str(ObjectId()),
            content="Hello, world!"
        )
        
        assert message_id == str(test_id)
        mock_col.insert_one.assert_called_once()
    
    def test_find_by_pod(self, mock_collection):
        """Test finding messages by pod."""
        mock_col, message_model = mock_collection
        
        from bson import ObjectId
        pod_id = ObjectId()
        message_id = ObjectId()
        sender_id = ObjectId()
        
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__.return_value = [
            {
                "_id": message_id,
                "pod_id": pod_id,
                "sender_id": sender_id,
                "content": "Test message",
                "read_by": []
            }
        ]
        mock_col.find.return_value = mock_cursor
        
        messages = message_model.find_by_pod(str(pod_id), limit=10)
        
        assert len(messages) == 1
        assert messages[0]["content"] == "Test message"
    
    def test_mark_as_read(self, mock_collection):
        """Test marking message as read."""
        mock_col, message_model = mock_collection
        
        from bson import ObjectId
        message_id = ObjectId()
        user_id = ObjectId()
        mock_col.update_one.return_value.modified_count = 1
        
        result = message_model.mark_as_read(str(message_id), str(user_id))
        
        assert result is True
        mock_col.update_one.assert_called_once()

