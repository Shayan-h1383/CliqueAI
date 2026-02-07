"""Pod management routes."""
from flask import Blueprint, request, jsonify, g

from backend.models.pod import Pod
from backend.models.user import User
from backend.models.clique import Clique
from backend.services.pod_service import PodService
from backend.middleware.auth_middleware import require_auth


pods_bp = Blueprint('pods', __name__, url_prefix='/api/pods')


def _ensure_pods_for_user_cliques(user_id: str) -> None:
    """Create pods for any clique the user is in that has 3+ members but no pod yet."""
    clique_model = Clique()
    pod_service = PodService()
    for clique in clique_model.find_by_member(user_id):
        members = clique.get("members") or []
        if len(members) < 3 or clique.get("pod_id"):
            continue
        try:
            pod = pod_service.create_pod(
                user_id=members[0],
                match_type=clique.get("match_type", "evolve"),
                member_ids=members,
            )
            clique_model.set_pod_id(clique["_id"], pod["_id"])
        except Exception:
            continue


@pods_bp.route('/mine', methods=['GET'])
@require_auth
def get_my_pods():
    """Get all active pods where the current user is a member (supports multiple cliques)."""
    try:
        user_id = g.current_user_id
        _ensure_pods_for_user_cliques(user_id)
        pod_model = Pod()
        pods = pod_model.find_active_by_member(user_id)
        return jsonify({
            'pods': pods
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'code': 500
        }), 500


@pods_bp.route('/active', methods=['GET'])
@require_auth
def get_active_pod():
    """Get the current user's active pod."""
    try:
        user_id = g.current_user_id
        
        user_model = User()
        user = user_model.find_by_id(user_id)
        
        if not user:
            return jsonify({
                'error': 'User not found',
                'code': 404
            }), 404
        
        active_pod_id = user.get('active_pod_id')
        
        if not active_pod_id:
            return jsonify({
                'pod': None,
                'message': 'No active pod'
            }), 200
        
        pod_model = Pod()
        pod = pod_model.find_by_id(active_pod_id)
        
        if not pod:
            # Clear invalid active_pod_id
            user_model.set_active_pod(user_id, None)
            return jsonify({
                'pod': None,
                'message': 'Active pod not found'
            }), 200
        
        # Check if user is still a member
        if user_id not in pod.get('members', []):
            # Clear invalid active_pod_id
            user_model.set_active_pod(user_id, None)
            return jsonify({
                'pod': None,
                'message': 'User is not a member of active pod'
            }), 200
        
        return jsonify({
            'pod': pod
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Failed to get active pod: {str(e)}',
            'code': 500
        }), 500


@pods_bp.route('/<pod_id>', methods=['GET'])
@require_auth
def get_pod(pod_id: str):
    """Get pod details. User must be a member."""
    try:
        user_id = g.current_user_id
        
        pod_model = Pod()
        pod = pod_model.find_by_id(pod_id)
        
        if not pod:
            return jsonify({
                'error': 'Pod not found',
                'code': 404
            }), 404
        
        # Verify user is a member
        if user_id not in pod.get('members', []):
            return jsonify({
                'error': 'Access denied. You are not a member of this pod.',
                'code': 403
            }), 403
        
        return jsonify({
            'pod': pod
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Failed to get pod: {str(e)}',
            'code': 500
        }), 500


@pods_bp.route('/<pod_id>/leave', methods=['POST'])
@require_auth
def leave_pod(pod_id: str):
    """Leave a pod."""
    try:
        user_id = g.current_user_id
        
        pod_service = PodService()
        pod_service.leave_pod(user_id, pod_id)
        
        return jsonify({
            'message': 'Successfully left pod'
        }), 200
    
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'code': 400
        }), 400
    except Exception as e:
        return jsonify({
            'error': f'Failed to leave pod: {str(e)}',
            'code': 500
        }), 500


@pods_bp.route('/<pod_id>/expired', methods=['GET'])
@require_auth
def check_pod_expired(pod_id: str):
    """Check if a pod has expired. Also triggers cleanup of expired pods."""
    try:
        user_id = g.current_user_id
        
        pod_model = Pod()
        pod = pod_model.find_by_id(pod_id)
        
        if not pod:
            return jsonify({
                'error': 'Pod not found',
                'code': 404
            }), 404
        
        # Verify user is a member
        if user_id not in pod.get('members', []):
            return jsonify({
                'error': 'Access denied. You are not a member of this pod.',
                'code': 403
            }), 403
        
        # Check expiration
        pod_service = PodService()
        is_expired = pod_service.is_pod_expired(pod_id)
        
        # Trigger cleanup of expired pods
        pod_service.expire_pods()
        
        return jsonify({
            'expired': is_expired,
            'pod': pod
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Failed to check pod expiration: {str(e)}',
            'code': 500
        }), 500

