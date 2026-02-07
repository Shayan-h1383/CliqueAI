"""Message routes for sending and retrieving messages, with SocketIO support."""
from flask import Blueprint, request, jsonify, g
from pydantic import BaseModel, Field, ValidationError
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import html

from backend.models.message import Message
from backend.models.pod import Pod
from backend.models.user import User
from backend.middleware.auth_middleware import require_auth
from backend.services.auth_service import auth_service


messages_bp = Blueprint('messages', __name__, url_prefix='/api/messages')

# SocketIO instance will be initialized in app.py
socketio: SocketIO = None


def init_socketio(sio: SocketIO):
    """Initialize SocketIO instance for this module."""
    global socketio
    socketio = sio


class SendMessageRequest(BaseModel):
    """Request schema for sending a message."""
    pod_id: str = Field(..., description="ID of the pod")
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")


def sanitize_content(content: str) -> str:
    """Sanitize user-generated content to prevent XSS."""
    # Basic HTML escaping
    return html.escape(content)


def verify_pod_membership(user_id: str, pod_id: str) -> bool:
    """Verify that a user is a member of a pod."""
    pod_model = Pod()
    pod = pod_model.find_by_id(pod_id)
    
    if not pod:
        return False
    
    return user_id in pod.get('members', [])


@messages_bp.route('/send', methods=['POST'])
@require_auth
def send_message():
    """Send a message to a pod."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Request body is required',
                'code': 400
            }), 400
        
        # Validate request data
        try:
            message_data = SendMessageRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'code': 400,
                'details': e.errors()
            }), 400
        
        user_id = g.current_user_id
        
        # Verify user is a pod member
        if not verify_pod_membership(user_id, message_data.pod_id):
            return jsonify({
                'error': 'You are not a member of this pod',
                'code': 403
            }), 403
        
        # Sanitize content
        sanitized_content = sanitize_content(message_data.content)
        
        # Create message
        message_model = Message()
        message_id = message_model.create(
            pod_id=message_data.pod_id,
            sender_id=user_id,
            content=sanitized_content
        )
        
        # Fetch created message and add sender username
        message = message_model.find_by_id(message_id)
        user_model = User()
        sender = user_model.find_by_id(user_id) if user_id else None
        message['sender_username'] = sender.get('username', 'Unknown') if sender else 'Unknown'

        # Emit SocketIO event to pod room
        if socketio:
            socketio.emit('new_message', {
                'message': message,
                'pod_id': message_data.pod_id
            }, room=f'pod_{message_data.pod_id}')
        
        return jsonify({
            'message': message
        }), 201
    
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'code': 400
        }), 400
    except Exception as e:
        return jsonify({
            'error': f'Failed to send message: {str(e)}',
            'code': 500
        }), 500


@messages_bp.route('/<pod_id>', methods=['GET'])
@require_auth
def get_messages(pod_id: str):
    """Get all messages for a pod (paginated)."""
    try:
        user_id = g.current_user_id
        
        # Verify user is a pod member
        if not verify_pod_membership(user_id, pod_id):
            return jsonify({
                'error': 'You are not a member of this pod',
                'code': 403
            }), 403
        
        # Get pagination parameters
        limit = request.args.get('limit', default=50, type=int)
        skip = request.args.get('skip', default=0, type=int)
        
        # Validate pagination
        if limit < 1 or limit > 100:
            limit = 50
        if skip < 0:
            skip = 0
        
        # Fetch messages
        message_model = Message()
        messages = message_model.find_by_pod(
            pod_id=pod_id,
            limit=limit,
            skip=skip
        )
        # Enrich with sender username for display
        user_model = User()
        for msg in messages:
            sender_id = msg.get('sender_id')
            if sender_id:
                sender = user_model.find_by_id(sender_id)
                msg['sender_username'] = sender.get('username', 'Unknown') if sender else 'Unknown'
            else:
                msg['sender_username'] = 'Unknown'

        return jsonify({
            'messages': messages,
            'count': len(messages),
            'limit': limit,
            'skip': skip
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Failed to get messages: {str(e)}',
            'code': 500
        }), 500


@messages_bp.route('/<message_id>/read', methods=['PUT'])
@require_auth
def mark_message_read(message_id: str):
    """Mark a message as read."""
    try:
        user_id = g.current_user_id
        
        message_model = Message()
        message = message_model.find_by_id(message_id)
        
        if not message:
            return jsonify({
                'error': 'Message not found',
                'code': 404
            }), 404
        
        pod_id = message.get('pod_id')
        
        # Verify user is a pod member
        if not verify_pod_membership(user_id, pod_id):
            return jsonify({
                'error': 'You are not a member of this pod',
                'code': 403
            }), 403
        
        # Mark as read
        success = message_model.mark_as_read(message_id, user_id)
        
        if not success:
            # Message might already be marked as read
            message = message_model.find_by_id(message_id)
        
        # Emit SocketIO event
        if socketio:
            socketio.emit('message_read', {
                'message_id': message_id,
                'user_id': user_id,
                'pod_id': pod_id
            }, room=f'pod_{pod_id}')
        
        return jsonify({
            'message': message_model.find_by_id(message_id)
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Failed to mark message as read: {str(e)}',
            'code': 500
        }), 500


# SocketIO event handlers
def register_socketio_handlers(sio: SocketIO):
    """Register SocketIO event handlers."""
    
    @sio.on('connect')
    def handle_connect(auth):
        """Handle client connection. Authenticate via JWT from query params."""
        try:
            token = request.args.get('token')
            if not token:
                disconnect()
                return False
            
            # Verify token
            payload = auth_service.verify_token(token)
            if not payload:
                disconnect()
                return False
            
            # Store user_id in session
            from flask import session
            session['user_id'] = payload.get('user_id')
            
            return True
        except Exception:
            disconnect()
            return False
    
    @sio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        pass
    
    @sio.on('join_pod')
    def handle_join_pod(data):
        """Join a pod room for real-time updates."""
        try:
            from flask import session
            user_id = session.get('user_id')
            if not user_id:
                emit('error', {'message': 'Not authenticated'})
                return
            
            pod_id = data.get('pod_id')
            if not pod_id:
                emit('error', {'message': 'pod_id is required'})
                return
            
            # Verify user is a pod member
            if not verify_pod_membership(user_id, pod_id):
                emit('error', {'message': 'You are not a member of this pod'})
                return
            
            # Join room
            room = f'pod_{pod_id}'
            join_room(room)
            emit('joined_pod', {'pod_id': pod_id, 'room': room})
        
        except Exception as e:
            emit('error', {'message': f'Failed to join pod: {str(e)}'})
    
    @sio.on('leave_pod')
    def handle_leave_pod(data):
        """Leave a pod room."""
        try:
            pod_id = data.get('pod_id')
            if pod_id:
                room = f'pod_{pod_id}'
                leave_room(room)
                emit('left_pod', {'pod_id': pod_id})
        except Exception as e:
            emit('error', {'message': f'Failed to leave pod: {str(e)}'})

