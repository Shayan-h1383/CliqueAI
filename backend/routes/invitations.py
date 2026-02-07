"""Invitation routes: create, list, accept, reject clique invitations."""
from typing import Optional
from flask import Blueprint, request, jsonify, g
from pydantic import BaseModel, Field, ValidationError

from backend.services.invitation_service import InvitationService
from backend.models.invitation import Invitation
from backend.models.user import User
from backend.middleware.auth_middleware import require_auth

invitations_bp = Blueprint('invitations', __name__, url_prefix='/api/invitations')


class CreateInvitationsRequest(BaseModel):
    invitee_ids: list = Field(..., min_length=2, max_length=2, description="Exactly 2 user IDs to invite")
    match_type: str = Field(..., description="evolve, enjoy, or support")
    application_id: Optional[str] = Field(default=None)


@invitations_bp.route('', methods=['POST'])
@require_auth
def create_invitations():
    """Create clique invitations (inviter selects 2 invitees)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required', 'code': 400}), 400
        try:
            body = CreateInvitationsRequest(**data)
        except ValidationError as e:
            return jsonify({'error': 'Validation failed', 'code': 400, 'details': e.errors()}), 400
        if body.match_type not in ('evolve', 'enjoy', 'support'):
            return jsonify({'error': 'match_type must be one of: evolve, enjoy, support', 'code': 400}), 400

        inviter_id = g.current_user_id
        service = InvitationService()
        result = service.create_clique_invitations(
            inviter_id=inviter_id,
            invitee_ids=body.invitee_ids,
            match_type=body.match_type,
            application_id=body.application_id,
        )
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e), 'code': 400}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'code': 500}), 500


@invitations_bp.route('', methods=['GET'])
@require_auth
def list_invitations():
    """List pending invitations for current user (as invitee)."""
    try:
        invitee_id = g.current_user_id
        inv_model = Invitation()
        invitations = inv_model.find_pending_by_invitee(invitee_id)

        # Enrich with inviter username
        user_model = User()
        for inv in invitations:
            inviter = user_model.find_by_id(inv['inviter_id'])
            inv['inviter_username'] = inviter.get('username', 'Unknown') if inviter else 'Unknown'

        return jsonify({'invitations': invitations}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'code': 500}), 500


@invitations_bp.route('/<invitation_id>/accept', methods=['POST'])
@require_auth
def accept_invitation(invitation_id: str):
    """Accept a clique invitation."""
    try:
        invitee_id = g.current_user_id
        service = InvitationService()
        result = service.accept_invitation(invitation_id, invitee_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e), 'code': 400}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'code': 500}), 500


@invitations_bp.route('/<invitation_id>/reject', methods=['POST'])
@require_auth
def reject_invitation(invitation_id: str):
    """Reject a clique invitation."""
    try:
        invitee_id = g.current_user_id
        service = InvitationService()
        service.reject_invitation(invitation_id, invitee_id)
        return jsonify({'message': 'Invitation rejected'}), 200
    except ValueError as e:
        return jsonify({'error': str(e), 'code': 400}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'code': 500}), 500
