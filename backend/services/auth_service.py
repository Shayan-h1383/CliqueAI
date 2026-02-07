"""Authentication service for password hashing and JWT token management."""
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

# In-memory token blacklist (can be upgraded to Redis later)
_token_blacklist: set = set()


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize AuthService.
        
        Args:
            secret_key: JWT secret key. If not provided, reads from JWT_SECRET_KEY env var.
            
        Raises:
            ValueError: If secret key is not provided and not found in environment
        """
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY')
        if not self.secret_key:
            raise ValueError(
                "JWT_SECRET_KEY environment variable is not set. "
                "Please set it in your .env file or pass it as a parameter."
            )
        self.algorithm = 'HS256'
        self.token_expiration_hours = 24
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using werkzeug's password hashing.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        if not password:
            raise ValueError("Password cannot be empty")
        return generate_password_hash(password)
    
    def verify_password(self, password_hash: str, password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password_hash: Hashed password
            password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        if not password_hash or not password:
            return False
        return check_password_hash(password_hash, password)
    
    def generate_token(self, user_id: str) -> str:
        """
        Generate a JWT token for a user.
        
        Args:
            user_id: User ID to encode in token
            
        Returns:
            str: JWT token string
        """
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiration_hours),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            dict: Decoded token payload if valid, None otherwise
        """
        if not token:
            return None
        
        # Check if token is blacklisted
        if token in _token_blacklist:
            return None
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def blacklist_token(self, token: str) -> bool:
        """
        Add a token to the blacklist.
        
        Args:
            token: JWT token string to blacklist
            
        Returns:
            bool: True if token was added to blacklist
        """
        if token:
            _token_blacklist.add(token)
            return True
        return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted.
        
        Args:
            token: JWT token string
            
        Returns:
            bool: True if token is blacklisted
        """
        return token in _token_blacklist


# Global instance
auth_service = AuthService()

