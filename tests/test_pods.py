"""Tests for pod management endpoints."""
import pytest
from flask.testing import FlaskClient
from unittest.mock import patch, MagicMock
from bson import ObjectId

from backend.models.user import User
from backend.models.pod import Pod


def register_and_login(client: FlaskClient, user_data: dict) -> str:
    """Helper to register and login a user, returning the token."""
    client.post('/api/auth/register', json=user_data)
    login_response = client.post('/api/auth/login', json={
        'email': user_data['email'],
        'password': user_data['password']
    })
    return login_response.get_json()['token']


def test_get_active_pod_none(client: FlaskClient, test_db, sample_user_data):
    """Test getting active pod when user has none."""
    token = register_and_login(client, sample_user_data)
    
    response = client.get('/api/pods/active', headers={
        'Authorization': f'Bearer {token}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['pod'] is None


def test_create_pod_success(client: FlaskClient, test_db, sample_user_data, 
                           sample_user_data_2, sample_user_data_3):
    """Test successful pod creation."""
    # Register 3 users
    token1 = register_and_login(client, sample_user_data)
    token2 = register_and_login(client, sample_user_data_2)
    token3 = register_and_login(client, sample_user_data_3)
    
    # Get user IDs
    user1_response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {token1}'
    })
    user1_id = user1_response.get_json()['user']['_id']
    
    user2_response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {token2}'
    })
    user2_id = user2_response.get_json()['user']['_id']
    
    user3_response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {token3}'
    })
    user3_id = user3_response.get_json()['user']['_id']
    
    # Set up matching preferences for all users
    user_model = User()
    user_model.update_matching_preferences(
        user1_id, 'friendship', 'Looking for friends', [0.1] * 768
    )
    user_model.update_matching_preferences(
        user2_id, 'friendship', 'Looking for friends', [0.2] * 768
    )
    user_model.update_matching_preferences(
        user3_id, 'friendship', 'Looking for friends', [0.3] * 768
    )
    
    # Mock Gemini service
    with patch('backend.services.pod_service.GeminiService') as mock_gemini:
        mock_instance = MagicMock()
        mock_instance.generate_icebreaker.return_value = "Test icebreaker message"
        mock_gemini.return_value = mock_instance
        
        # Create pod
        response = client.post('/api/matching/create-pod', 
            json={
                'match_type': 'friendship',
                'member_ids': [user1_id, user2_id, user3_id]
            },
            headers={'Authorization': f'Bearer {token1}'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'pod' in data
        assert 'icebreaker' in data
        assert data['pod']['pod_type'] == 'friendship'
        assert len(data['pod']['members']) == 3


def test_create_pod_wrong_member_count(client: FlaskClient, test_db, sample_user_data):
    """Test pod creation with wrong number of members."""
    token = register_and_login(client, sample_user_data)
    
    user_response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {token}'
    })
    user_id = user_response.get_json()['user']['_id']
    
    # Try with 2 members
    response = client.post('/api/matching/create-pod',
        json={
            'match_type': 'friendship',
            'member_ids': [user_id, 'another_id']
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 400


def test_get_pod_success(client: FlaskClient, test_db, sample_user_data,
                         sample_user_data_2, sample_user_data_3):
    """Test getting pod details."""
    # Create a pod first (simplified - would need full setup)
    token1 = register_and_login(client, sample_user_data)
    user1_response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {token1}'
    })
    user1_id = user1_response.get_json()['user']['_id']
    
    # Create pod directly in database for testing (use valid ObjectIds)
    other1, other2 = str(ObjectId()), str(ObjectId())
    pod_model = Pod()
    pod_id = pod_model.create(
        pod_type='friendship',
        member_ids=[user1_id, other1, other2],
        gemini_icebreaker='Test icebreaker'
    )
    
    # Get pod
    response = client.get(f'/api/pods/{pod_id}', headers={
        'Authorization': f'Bearer {token1}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'pod' in data
    assert data['pod']['_id'] == pod_id


def test_leave_pod_success(client: FlaskClient, test_db, sample_user_data):
    """Test leaving a pod."""
    token = register_and_login(client, sample_user_data)
    user_response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {token}'
    })
    user_id = user_response.get_json()['user']['_id']
    
    # Create pod with user as member (use valid ObjectIds for other members)
    other1, other2 = str(ObjectId()), str(ObjectId())
    pod_model = Pod()
    pod_id = pod_model.create(
        pod_type='friendship',
        member_ids=[user_id, other1, other2],
        gemini_icebreaker='Test icebreaker'
    )
    
    # Set user's active pod
    user_model = User()
    user_model.set_active_pod(user_id, pod_id)
    
    # Leave pod
    response = client.post(f'/api/pods/{pod_id}/leave', headers={
        'Authorization': f'Bearer {token}'
    })
    
    assert response.status_code == 200
    
    # Verify user's active_pod_id is cleared
    user = user_model.find_by_id(user_id)
    assert user.get('active_pod_id') is None


def test_check_pod_expired(client: FlaskClient, test_db, sample_user_data):
    """Test checking if pod is expired."""
    token = register_and_login(client, sample_user_data)
    user_response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {token}'
    })
    user_id = user_response.get_json()['user']['_id']
    
    # Create pod (use valid ObjectIds for other members)
    other1, other2 = str(ObjectId()), str(ObjectId())
    pod_model = Pod()
    pod_id = pod_model.create(
        pod_type='friendship',
        member_ids=[user_id, other1, other2],
        gemini_icebreaker='Test icebreaker'
    )
    
    # Check expiration
    response = client.get(f'/api/pods/{pod_id}/expired', headers={
        'Authorization': f'Bearer {token}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'expired' in data
    assert 'pod' in data

