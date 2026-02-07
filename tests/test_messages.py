"""Tests for message endpoints."""
import pytest
from flask.testing import FlaskClient
from bson import ObjectId

from backend.models.user import User
from backend.models.pod import Pod
from backend.models.message import Message


def register_and_login(client: FlaskClient, user_data: dict) -> str:
    """Helper to register and login a user, returning the token."""
    client.post('/api/auth/register', json=user_data)
    login_response = client.post('/api/auth/login', json={
        'email': user_data['email'],
        'password': user_data['password']
    })
    return login_response.get_json()['token']


def test_send_message_success(client: FlaskClient, test_db, sample_user_data):
    """Test sending a message to a pod."""
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
    
    # Send message
    response = client.post('/api/messages/send',
        json={
            'pod_id': pod_id,
            'content': 'Hello, this is a test message!'
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'message' in data
    assert data['message']['content'] == 'Hello, this is a test message!'
    assert data['message']['sender_id'] == user_id
    assert str(data['message']['pod_id']) == str(pod_id)


def test_send_message_not_member(client: FlaskClient, test_db, sample_user_data):
    """Test sending message when user is not a pod member."""
    token = register_and_login(client, sample_user_data)
    
    # Create pod without user as member (use valid ObjectIds)
    member_ids = [str(ObjectId()), str(ObjectId()), str(ObjectId())]
    pod_model = Pod()
    pod_id = pod_model.create(
        pod_type='friendship',
        member_ids=member_ids,
        gemini_icebreaker='Test icebreaker'
    )
    
    # Try to send message
    response = client.post('/api/messages/send',
        json={
            'pod_id': pod_id,
            'content': 'Hello!'
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 403


def test_get_messages_success(client: FlaskClient, test_db, sample_user_data):
    """Test getting messages for a pod."""
    token = register_and_login(client, sample_user_data)
    user_response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {token}'
    })
    user_id = user_response.get_json()['user']['_id']
    
    # Create pod and send some messages (use valid ObjectIds for other members)
    other1, other2 = str(ObjectId()), str(ObjectId())
    pod_model = Pod()
    pod_id = pod_model.create(
        pod_type='friendship',
        member_ids=[user_id, other1, other2],
        gemini_icebreaker='Test icebreaker'
    )
    
    message_model = Message()
    message_model.create(pod_id, user_id, 'Message 1')
    message_model.create(pod_id, user_id, 'Message 2')
    
    # Get messages
    response = client.get(f'/api/messages/{pod_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'messages' in data
    assert len(data['messages']) == 2


def test_get_messages_paginated(client: FlaskClient, test_db, sample_user_data):
    """Test getting messages with pagination."""
    token = register_and_login(client, sample_user_data)
    user_response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {token}'
    })
    user_id = user_response.get_json()['user']['_id']
    
    # Create pod and send multiple messages (use valid ObjectIds for other members)
    other1, other2 = str(ObjectId()), str(ObjectId())
    pod_model = Pod()
    pod_id = pod_model.create(
        pod_type='friendship',
        member_ids=[user_id, other1, other2],
        gemini_icebreaker='Test icebreaker'
    )
    
    message_model = Message()
    for i in range(10):
        message_model.create(pod_id, user_id, f'Message {i}')
    
    # Get messages with limit
    response = client.get(f'/api/messages/{pod_id}?limit=5',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['messages']) == 5


def test_mark_message_read_success(client: FlaskClient, test_db, sample_user_data):
    """Test marking a message as read."""
    token = register_and_login(client, sample_user_data)
    user_response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {token}'
    })
    user_id = user_response.get_json()['user']['_id']
    
    # Create pod and message (other_sender is a valid member who sent the message)
    other_sender, other2 = str(ObjectId()), str(ObjectId())
    pod_model = Pod()
    pod_id = pod_model.create(
        pod_type='friendship',
        member_ids=[user_id, other_sender, other2],
        gemini_icebreaker='Test icebreaker'
    )
    
    message_model = Message()
    message_id = message_model.create(pod_id, other_sender, 'Test message')
    
    # Mark as read
    response = client.put(f'/api/messages/{message_id}/read',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert user_id in data['message'].get('read_by', [])


def test_mark_message_read_not_member(client: FlaskClient, test_db, sample_user_data):
    """Test marking message as read when user is not a pod member."""
    token = register_and_login(client, sample_user_data)
    
    # Create pod without user as member (use valid ObjectIds)
    member_ids = [str(ObjectId()), str(ObjectId()), str(ObjectId())]
    pod_model = Pod()
    pod_id = pod_model.create(
        pod_type='friendship',
        member_ids=member_ids,
        gemini_icebreaker='Test icebreaker'
    )
    
    message_model = Message()
    message_id = message_model.create(pod_id, member_ids[0], 'Test message')
    
    # Try to mark as read
    response = client.put(f'/api/messages/{message_id}/read',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 403

