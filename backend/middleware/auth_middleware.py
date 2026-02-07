"""Authentication middleware for protecting routes with JWT tokens."""
from functools import wraps
from flask import request, jsonify, g
from typing import Callable, Any

from backend.services.auth_service import auth_service


def require_auth(f: Callable) -> Callable:
    """
    Decorator to protect routes that require authentication.
    
    Extracts JWT token from Authorization header, validates it,
    and injects current_user_id into Flask's g object.
    
    Usage:
        @require_auth
        def protected_route():
            user_id = g.current_user_id
            ...
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'error': 'Authorization header is missing',
                'code': 401
            }), 401
        
        # Check if header starts with 'Bearer '
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Invalid authorization header format. Expected: Bearer <token>',
                'code': 401
            }), 401
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        # Verify token
        payload = auth_service.verify_token(token)
        
        if not payload:
            return jsonify({
                'error': 'Invalid or expired token',
                'code': 401
            }), 401
        
        # Inject user_id into Flask's g object
        g.current_user_id = payload.get('user_id')
        
        if not g.current_user_id:
            return jsonify({
                'error': 'Token payload is invalid',
                'code': 401
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

