"""Invitation service: create clique invitations, accept/reject, pod creation on both accept."""
import uuid
from typing import List, Dict, Optional

from backend.models.invitation import Invitation
from backend.models.user import User
from backend.services.pod_service import PodService


class InvitationService:
    def __init__(self):
        self.invitation_model = Invitation()
        self.user_model = User()
        self.pod_service = PodService()

    def create_clique_invitations(
        self,
        inviter_id: str,
        invitee_ids: List[str],
        match_type: str,
        application_id: Optional[str] = None,
    ) -> Dict:
        """
        Create 2 invitations with shared clique_group_id.
        invitee_ids must have exactly 2 user IDs.
        """
        if len(invitee_ids) != 2:
            raise ValueError("Must invite exactly 2 users")
        if inviter_id in invitee_ids:
            raise ValueError("Cannot invite yourself")

        clique_group_id = str(uuid.uuid4())
        created = []
        for invitee_id in invitee_ids:
            inv_id = self.invitation_model.create(
                inviter_id=inviter_id,
                invitee_id=invitee_id,
                clique_group_id=clique_group_id,
                match_type=match_type,
                application_id=application_id,
            )
            created.append(inv_id)

        return {
            "clique_group_id": clique_group_id,
            "invitation_ids": created,
            "invitee_ids": invitee_ids,
        }

    def accept_invitation(self, invitation_id: str, invitee_id: str) -> Dict:
        """
        Accept an invitation. If both invitees in the group have accepted, create pod.
        Returns { accepted: True, pod: {...} or None }
        """
        inv = self.invitation_model.find_by_id(invitation_id)
        if not inv:
            raise ValueError("Invitation not found")
        if inv["invitee_id"] != invitee_id:
            raise ValueError("Not authorized to accept this invitation")
        if inv["status"] != "pending":
            raise ValueError("Invitation is no longer pending")

        ok = self.invitation_model.update_status(invitation_id, "accepted")
        if not ok:
            raise ValueError("Failed to accept invitation")

        group = self.invitation_model.find_by_clique_group_id(inv["clique_group_id"])
        accepted_count = sum(1 for g in group if g["status"] == "accepted")

        if accepted_count == 2:
            # Both accepted: create pod
            inviter_id = inv["inviter_id"]
            invitee_ids = [g["invitee_id"] for g in group]
            member_ids = [inviter_id] + invitee_ids
            pod = self.pod_service.create_pod(
                user_id=inviter_id,
                match_type=inv["match_type"],
                member_ids=member_ids,
            )
            return {"accepted": True, "pod": pod}

        return {"accepted": True, "pod": None}

    def reject_invitation(self, invitation_id: str, invitee_id: str) -> None:
        """
        Reject an invitation. Auto-cancels the other invitation in the same group.
        """
        inv = self.invitation_model.find_by_id(invitation_id)
        if not inv:
            raise ValueError("Invitation not found")
        if inv["invitee_id"] != invitee_id:
            raise ValueError("Not authorized to reject this invitation")
        if inv["status"] != "pending":
            raise ValueError("Invitation is no longer pending")

        ok = self.invitation_model.update_status(invitation_id, "rejected")
        if not ok:
            raise ValueError("Failed to reject invitation")

        # Cancel other invitation in same group
        self.invitation_model.cancel_group(inv["clique_group_id"])
