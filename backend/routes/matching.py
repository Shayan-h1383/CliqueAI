"""Matching routes for finding matches and creating pods."""
from flask import Blueprint, request, jsonify, g, current_app
from pydantic import BaseModel, Field, ValidationError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from backend.services.matching_service import MatchingService
from backend.services.pod_service import PodService
from backend.middleware.auth_middleware import require_auth


matching_bp = Blueprint('matching', __name__, url_prefix='/api/matching')

# Rate limiter will be initialized in app.py
limiter = None


def init_limiter(app_limiter: Limiter):
    """Initialize rate limiter for this module."""
    global limiter
    limiter = app_limiter
    # Apply rate limit to find_matches function if it exists
    if limiter and 'find_matches' in matching_bp.view_functions:
        matching_bp.view_functions['find_matches'] = limiter.limit("10 per minute")(
            matching_bp.view_functions['find_matches']
        )


class FindMatchesRequest(BaseModel):
    """Request schema for finding matches."""
    match_type: str = Field(..., description="Type of match: evolve, enjoy, or support")
    focus_text: str = Field(..., min_length=1, description="User's input describing their current need")
    
    @classmethod
    def validate_match_type(cls, v: str) -> str:
        """Validate match_type."""
        if v not in ['evolve', 'enjoy', 'support']:
            raise ValueError("match_type must be one of: evolve, enjoy, support")
        return v


class CreatePodRequest(BaseModel):
    """Request schema for creating a pod."""
    match_type: str = Field(..., description="Type of pod: evolve, enjoy, or support")
    member_ids: list = Field(..., min_length=3, max_length=3, description="List of exactly 3 user IDs")
    
    @classmethod
    def validate_match_type(cls, v: str) -> str:
        """Validate match_type."""
        if v not in ['evolve', 'enjoy', 'support']:
            raise ValueError("match_type must be one of: evolve, enjoy, support")
        return v


@matching_bp.route('/find', methods=['POST'])
@require_auth
def find_matches():
    """Find matches for the current user based on semantic similarity. Rate limited to 10 per minute."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Request body is required',
                'code': 400
            }), 400
        
        # Validate request data
        try:
            find_data = FindMatchesRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'code': 400,
                'details': e.errors()
            }), 400
        
        # Validate match_type
        if find_data.match_type not in ['evolve', 'enjoy', 'support']:
            return jsonify({
                'error': 'match_type must be one of: evolve, enjoy, support',
                'code': 400
            }), 400
        
        user_id = g.current_user_id
        
        # Find matches
        matching_service = MatchingService()
        matches = matching_service.find_matches(
            user_id=user_id,
            match_type=find_data.match_type,
            focus_text=find_data.focus_text
        )
        
        # Get user's embedding for response
        from backend.models.user import User
        user_model = User()
        user = user_model.find_by_id(user_id)
        user_embedding = None
        if user:
            user_embedding = user.get('matching_preferences', {}).get('focus_embedding')
        
        return jsonify({
            'matches': matches,
            'user_embedding': user_embedding
        }), 200
    
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'code': 400
        }), 400
    except Exception as e:
        return jsonify({
            'error': f'Failed to find matches: {str(e)}',
            'code': 500
        }), 500


@matching_bp.route('/create-pod', methods=['POST'])
@require_auth
def create_pod():
    """Create a pod from selected matches."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Request body is required',
                'code': 400
            }), 400
        
        # Validate request data
        try:
            pod_data = CreatePodRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'code': 400,
                'details': e.errors()
            }), 400
        
        # Validate match_type
        if pod_data.match_type not in ['evolve', 'enjoy', 'support']:
            return jsonify({
                'error': 'match_type must be one of: evolve, enjoy, support',
                'code': 400
            }), 400
        
        # Validate exactly 3 members
        if len(pod_data.member_ids) != 3:
            return jsonify({
                'error': 'Pod must have exactly 3 members',
                'code': 400
            }), 400
        
        user_id = g.current_user_id
        
        # Verify requester is in member list
        if user_id not in pod_data.member_ids:
            return jsonify({
                'error': 'Requester must be included in member_ids',
                'code': 400
            }), 400
        
        # Create pod
        pod_service = PodService()
        pod = pod_service.create_pod(
            user_id=user_id,
            match_type=pod_data.match_type,
            member_ids=pod_data.member_ids
        )
        
        return jsonify({
            'pod': pod,
            'icebreaker': pod.get('gemini_icebreaker')
        }), 201
    
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'code': 400
        }), 400
    except Exception as e:
        return jsonify({
            'error': f'Failed to create pod: {str(e)}',
            'code': 500
        }), 500

