"""Clique application routes: submit, list mine, get one with linked suggestions, admin reject."""
from typing import Optional
from flask import Blueprint, request, jsonify, g
from pydantic import BaseModel, Field, ValidationError

from backend.models.application import CliqueApplication, GOALS
from backend.models.user import User
from backend.models.invitation import Invitation
from backend.models.clique import Clique
from backend.services.application_matching_service import ApplicationMatchingService
from backend.middleware.auth_middleware import require_auth

applications_bp = Blueprint('applications', __name__, url_prefix='/api/applications')

# Evolve areas
EVOLVE_AREAS = ["studies", "business", "arts development", "sports", "general"]
# Enjoy areas (interests/hobbies)
ENJOY_AREAS = ["gaming", "content", "humour", "hiking", "camping", "sports"]
# Support areas (struggles)
SUPPORT_AREAS = ["addiction", "relationship", "grief", "illness", "general depression", "other"]

# Minimum total word count for details + third_field so embeddings are specific enough for matching
MIN_DESCRIPTION_WORDS = 15


class SubmitApplicationRequest(BaseModel):
    goal: str = Field(..., description="evolve, enjoy, or support")
    area: str = Field(..., min_length=1)
    details: str = Field(..., min_length=1, max_length=500)
    third_field: str = Field(..., max_length=100, description="your_goal / how_enjoy_together / resolution_redemption")
    city: str = Field(..., min_length=1)


@applications_bp.route('', methods=['POST'])
@require_auth
def submit_application():
    """Submit a clique application; runs matching and returns application with linked_applications if any."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required', 'code': 400}), 400
        try:
            body = SubmitApplicationRequest(**data)
        except ValidationError as e:
            return jsonify({'error': 'Validation failed', 'code': 400, 'details': e.errors()}), 400
        if body.goal not in GOALS:
            return jsonify({'error': f'goal must be one of: {GOALS}', 'code': 400}), 400
        combined = f"{body.details.strip()} {body.third_field.strip()}"
        word_count = len(combined.split())
        if word_count < MIN_DESCRIPTION_WORDS:
            return jsonify({
                'error': 'Please add a bit more detail about your situation and goal so we can find better matches.',
                'code': 400,
            }), 400
        user_id = g.current_user_id
        service = ApplicationMatchingService()
        application = service.submit_and_match(
            user_id=user_id,
            goal=body.goal,
            area=body.area.strip(),
            details=body.details.strip(),
            third_field=body.third_field.strip(),
            city=body.city.strip(),
        )
        # Enrich linked_applications with user info and invitation status
        application = _enrich_linked(application, user_id)
        return jsonify(application), 201
    except ValueError as e:
        return jsonify({'error': str(e), 'code': 400}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'code': 500}), 500


@applications_bp.route('', methods=['GET'])
@require_auth
def list_my_applications():
    """List current user's clique applications."""
    try:
        user_id = g.current_user_id
        app_model = CliqueApplication()
        applications = app_model.find_by_user_id(user_id)
        for app in applications:
            _enrich_linked(app, user_id)
        return jsonify(applications), 200
    except Exception as e:
        return jsonify({'error': str(e), 'code': 500}), 500


@applications_bp.route('/<application_id>', methods=['GET'])
@require_auth
def get_application(application_id):
    """Get one application by id; must belong to current user. Returns linked applications enriched with user info."""
    try:
        user_id = g.current_user_id
        app_model = CliqueApplication()
        application = app_model.find_by_id(application_id)
        if not application:
            return jsonify({'error': 'Application not found', 'code': 404}), 404
        if application['user_id'] != user_id:
            return jsonify({'error': 'Forbidden', 'code': 403}), 403
        application = _enrich_linked(application, user_id)
        return jsonify(application), 200
    except Exception as e:
        return jsonify({'error': str(e), 'code': 500}), 500


@applications_bp.route('/<application_id>', methods=['PATCH'])
@require_auth
def update_application(application_id):
    """Admin: reject application (status=rejected, optional rejected_reason)."""
    try:
        data = request.get_json() or {}
        status = data.get('status')
        if status != 'rejected':
            return jsonify({'error': 'Only status=rejected is supported', 'code': 400}), 400
        app_model = CliqueApplication()
        application = app_model.find_by_id(application_id)
        if not application:
            return jsonify({'error': 'Application not found', 'code': 404}), 404
        reason = data.get('rejected_reason', '')
        ok = app_model.update_status(application_id, 'rejected', rejected_reason=reason)
        if not ok:
            return jsonify({'error': 'Update failed', 'code': 500}), 500
        return jsonify(app_model.find_by_id(application_id)), 200
    except Exception as e:
        return jsonify({'error': str(e), 'code': 500}), 500


def _invitation_status(
    current_user_id: str,
    other_user_id: str,
    application_id: Optional[str] = None,
) -> str:
    """Returns: none, pending_them, pending_me, accepted, rejected. Scoped by application_id when provided."""
    if not other_user_id:
        return "none"
    # If we're in the same clique (or pod), we're connected regardless of invitation state
    clique_model = Clique()
    if clique_model.find_containing_both(current_user_id, other_user_id):
        return "accepted"
    inv_model = Invitation()
    inv = inv_model.find_any_between(current_user_id, other_user_id, application_id=application_id)
    if not inv:
        return "none"
    status = inv.get("status") or "pending"
    if status == "accepted":
        return "accepted"
    if status == "rejected":
        return "rejected"
    if inv["invitee_id"] == current_user_id:
        return "pending_them"
    return "pending_me"


def _enrich_linked(application: dict, current_user_id: str) -> dict:
    """Add username, profile_pic_url, payload, and invitation_status. Exclude self from list."""
    linked = application.get('linked_applications') or []
    user_model = User()
    app_model = CliqueApplication()
    application_id = application.get('_id')
    enriched = []
    for entry in linked:
        app_id = entry.get('application_id')
        other = app_model.find_by_id(app_id) if app_id else None
        other_user_id = str(other['user_id']) if other else None
        if not other_user_id or other_user_id == current_user_id:
            continue
        user = user_model.find_by_id(other_user_id)
        enriched.append({
            **entry,
            'user_id': other_user_id,
            'username': user.get('username', 'Unknown') if user else 'Unknown',
            'profile_pic_url': user.get('profile', {}).get('profile_pic_url') if user else None,
            'payload': other.get('payload') if other else None,
            'invitation_status': _invitation_status(current_user_id, other_user_id, application_id),
        })
    application['linked_applications'] = enriched
    return application
