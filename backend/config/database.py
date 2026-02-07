"""MongoDB database connection configuration."""
import os
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ConfigurationError
from dotenv import load_dotenv

load_dotenv()


class DatabaseConnection:
    """Singleton class for MongoDB connection management."""
    
    _instance: Optional['DatabaseConnection'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    def __new__(cls) -> 'DatabaseConnection':
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize database connection if not already connected."""
        # Don't connect immediately - use lazy loading
        pass
    
    def _connect(self) -> None:
        """Establish MongoDB connection."""
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            raise ConfigurationError(
                "MONGODB_URI environment variable is not set. "
                "Please set it in your .env file."
            )
        
        try:
            self._client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self._client.admin.command('ping')
            # Extract database name from URI or use default
            db_name = mongodb_uri.split('/')[-1].split('?')[0] or 'hacketon'
            self._db = self._client[db_name]
        except ConnectionFailure as e:
            raise ConnectionFailure(
                f"Failed to connect to MongoDB: {str(e)}"
            ) from e
    
    @property
    def client(self) -> MongoClient:
        """Get MongoDB client instance."""
        if self._client is None:
            self._connect()
        return self._client
    
    @property
    def db(self) -> Database:
        """Get database instance."""
        if self._db is None:
            self._connect()
        return self._db
    
    def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def close(self) -> None:
        """Close database connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None


# Global database instance (lazy-loaded, connects on first access)
db_connection = DatabaseConnection()

