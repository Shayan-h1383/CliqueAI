"""Tests for authentication endpoints."""
import pytest
from flask import Flask
from flask.testing import FlaskClient

from backend.models.user import User
from backend.services.auth_service import auth_service


def test_register_success(client: FlaskClient, test_db, sample_user_data):
    """Test successful user registration."""
    response = client.post('/api/auth/register', json=sample_user_data)
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'user' in data
    assert data['user']['username'] == sample_user_data['username']
    assert data['user']['email'] == sample_user_data['email']
    assert 'password_hash' not in data['user']


def test_register_duplicate_username(client: FlaskClient, test_db, sample_user_data):
    """Test registration with duplicate username."""
    # Register first user
    client.post('/api/auth/register', json=sample_user_data)
    
    # Try to register with same username
    duplicate_data = sample_user_data.copy()
    duplicate_data['email'] = 'different@example.com'
    response = client.post('/api/auth/register', json=duplicate_data)
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'already exists' in data['error'].lower()


def test_register_duplicate_email(client: FlaskClient, test_db, sample_user_data):
    """Test registration with duplicate email."""
    # Register first user
    client.post('/api/auth/register', json=sample_user_data)
    
    # Try to register with same email
    duplicate_data = sample_user_data.copy()
    duplicate_data['username'] = 'differentuser'
    response = client.post('/api/auth/register', json=duplicate_data)
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_register_invalid_data(client: FlaskClient, test_db):
    """Test registration with invalid data."""
    # Missing required fields
    response = client.post('/api/auth/register', json={'username': 'test'})
    assert response.status_code == 400
    
    # Invalid email
    response = client.post('/api/auth/register', json={
        'username': 'test',
        'email': 'invalid-email',
        'password': 'pass'
    })
    assert response.status_code == 400
    
    # Password too short
    response = client.post('/api/auth/register', json={
        'username': 'test',
        'email': 'test@example.com',
        'password': '12345'  # Less than 6 characters
    })
    assert response.status_code == 400


def test_login_success(client: FlaskClient, test_db, sample_user_data):
    """Test successful login."""
    # Register user first
    client.post('/api/auth/register', json=sample_user_data)
    
    # Login
    response = client.post('/api/auth/login', json={
        'email': sample_user_data['email'],
        'password': sample_user_data['password']
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'token' in data
    assert 'user' in data
    assert data['user']['email'] == sample_user_data['email']


def test_login_invalid_credentials(client: FlaskClient, test_db, sample_user_data):
    """Test login with invalid credentials."""
    # Register user first
    client.post('/api/auth/register', json=sample_user_data)
    
    # Try wrong password
    response = client.post('/api/auth/login', json={
        'email': sample_user_data['email'],
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data
    
    # Try non-existent email
    response = client.post('/api/auth/login', json={
        'email': 'nonexistent@example.com',
        'password': 'password'
    })
    
    assert response.status_code == 401


def test_logout_success(client: FlaskClient, test_db, sample_user_data):
    """Test successful logout."""
    # Register and login
    client.post('/api/auth/register', json=sample_user_data)
    login_response = client.post('/api/auth/login', json={
        'email': sample_user_data['email'],
        'password': sample_user_data['password']
    })
    token = login_response.get_json()['token']
    
    # Logout
    response = client.post('/api/auth/logout', headers={
        'Authorization': f'Bearer {token}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    
    # Verify token is blacklisted
    assert auth_service.is_token_blacklisted(token)


def test_get_current_user_success(client: FlaskClient, test_db, sample_user_data):
    """Test getting current user profile."""
    # Register and login
    client.post('/api/auth/register', json=sample_user_data)
    login_response = client.post('/api/auth/login', json={
        'email': sample_user_data['email'],
        'password': sample_user_data['password']
    })
    token = login_response.get_json()['token']
    
    # Get current user
    response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {token}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'user' in data
    assert data['user']['email'] == sample_user_data['email']


def test_get_current_user_no_token(client: FlaskClient, test_db):
    """Test getting current user without token."""
    response = client.get('/api/auth/me')
    
    assert response.status_code == 401


def test_get_current_user_invalid_token(client: FlaskClient, test_db):
    """Test getting current user with invalid token."""
    response = client.get('/api/auth/me', headers={
        'Authorization': 'Bearer invalid-token'
    })
    
    assert response.status_code == 401


def test_get_current_user_blacklisted_token(client: FlaskClient, test_db, sample_user_data):
    """Test getting current user with blacklisted token."""
    # Register and login
    client.post('/api/auth/register', json=sample_user_data)
    login_response = client.post('/api/auth/login', json={
        'email': sample_user_data['email'],
        'password': sample_user_data['password']
    })
    token = login_response.get_json()['token']
    
    # Logout (blacklist token)
    client.post('/api/auth/logout', headers={
        'Authorization': f'Bearer {token}'
    })
    
    # Try to use blacklisted token
    response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {token}'
    })
    
    assert response.status_code == 401

