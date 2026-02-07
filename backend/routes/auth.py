"""Authentication routes for user registration, login, logout, and profile."""
from flask import Blueprint, request, jsonify, g
from pydantic import BaseModel, EmailStr, Field, ValidationError

from backend.models.user import User, UserSchema
from backend.services.auth_service import auth_service
from backend.middleware.auth_middleware import require_auth
from pymongo.errors import DuplicateKeyError


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


class RegisterRequest(BaseModel):
    """Request schema for user registration."""
    username: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class LoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Request body is required',
                'code': 400
            }), 400
        
        # Validate request data
        try:
            register_data = RegisterRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'code': 400,
                'details': e.errors()
            }), 400
        
        # Hash password
        password_hash = auth_service.hash_password(register_data.password)
        
        # Create user
        user_model = User()
        user_data = {
            'username': register_data.username,
            'email': register_data.email,
            'password_hash': password_hash
        }
        
        try:
            user_id = user_model.create(user_data)
        except DuplicateKeyError:
            return jsonify({
                'error': 'Username or email already exists',
                'code': 400
            }), 400
        
        # Fetch created user (excluding password_hash)
        user = user_model.find_by_id(user_id)
        if not user:
            return jsonify({
                'error': 'Failed to create user',
                'code': 500
            }), 500
        
        # Remove sensitive data
        user.pop('password_hash', None)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user
        }), 201
    
    except Exception as e:
        return jsonify({
            'error': f'Registration failed: {str(e)}',
            'code': 500
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Request body is required',
                'code': 400
            }), 400
        
        # Validate request data
        try:
            login_data = LoginRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'code': 400,
                'details': e.errors()
            }), 400
        
        # Find user by email
        user_model = User()
        user = user_model.find_by_email(login_data.email)
        
        if not user:
            return jsonify({
                'error': 'Invalid email or password',
                'code': 401
            }), 401
        
        # Verify password
        password_hash = user.get('password_hash')
        if not password_hash or not auth_service.verify_password(password_hash, login_data.password):
            return jsonify({
                'error': 'Invalid email or password',
                'code': 401
            }), 401
        
        # Generate JWT token
        user_id = str(user['_id'])
        token = auth_service.generate_token(user_id)
        
        # Remove sensitive data
        user.pop('password_hash', None)
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Login failed: {str(e)}',
            'code': 500
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user by blacklisting their token."""
    try:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            auth_service.blacklist_token(token)
        
        return jsonify({
            'message': 'Logout successful'
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Logout failed: {str(e)}',
            'code': 500
        }), 500


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current authenticated user's profile."""
    try:
        user_id = g.current_user_id
        
        user_model = User()
        user = user_model.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'error': 'User not found',
                'code': 404
            }), 404
        
        # Remove sensitive data
        user.pop('password_hash', None)
        
        return jsonify({
            'user': user
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Failed to get user profile: {str(e)}',
            'code': 500
        }), 500

