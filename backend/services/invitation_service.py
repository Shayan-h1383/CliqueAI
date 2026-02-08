"""Invitation service: per-suggestion accept/reject, clique creation, pod when clique >= 3."""
import uuid
from typing import List, Dict, Optional

from backend.models.invitation import Invitation
from backend.models.user import User
from backend.models.clique import Clique, MAX_CLIQUE_MEMBERS
from backend.services.pod_service import PodService


class InvitationService:
    def __init__(self):
        self.invitation_model = Invitation()
        self.user_model = User()
        self.clique_model = Clique()
        self.pod_service = PodService()

    def create_clique_invitations(
        self,
        inviter_id: str,
        invitee_ids: List[str],
        match_type: str,
        application_id: Optional[str] = None,
    ) -> Dict:
        """
        Create 2 invitations with shared clique_group_id (legacy: select 2 and send).
        When both accept, create clique of 3 and pod.
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

    def respond_to_suggestion(
        self,
        my_id: str,
        other_user_id: str,
        accept: bool,
        match_type: str = "evolve",
        application_id: Optional[str] = None,
    ) -> Dict:
        """
        Accept or reject a suggestion (one other user). If accept: accept their invitation
        if one exists (then mutual → clique), else create my invitation to them.
        If reject: reject their invitation if one exists.
        Returns { accepted, rejected, invitation, pod?, clique? }
        """
        if my_id == other_user_id:
            raise ValueError("Cannot respond to yourself")
        pending_from_them = self.invitation_model.find_pending_from_inviter_to_invitee(
            inviter_id=other_user_id,
            invitee_id=my_id,
            application_id=application_id,
        )
        if accept:
            if pending_from_them:
                # They invited me; accepting creates mutual → clique
                result = self.accept_invitation(pending_from_them["_id"], my_id)
                return {
                    "accepted": True,
                    "rejected": False,
                    "invitation_id": pending_from_them["_id"],
                    "pod": result.get("pod"),
                    "clique": result.get("clique"),
                }
            # I'm inviting them; create invitation me → other
            clique_group_id = str(uuid.uuid4())
            inv_id = self.invitation_model.create(
                inviter_id=my_id,
                invitee_id=other_user_id,
                clique_group_id=clique_group_id,
                match_type=match_type,
                application_id=application_id,
            )
            return {
                "accepted": True,
                "rejected": False,
                "invitation_id": inv_id,
                "pending_them": True,
                "pod": None,
                "clique": None,
            }
        # Reject
        if pending_from_them:
            self.invitation_model.update_status(pending_from_them["_id"], "rejected")
            return {"accepted": False, "rejected": True, "invitation_id": pending_from_them["_id"]}
        return {"accepted": False, "rejected": True}

    def _ensure_clique_and_pod(
        self,
        user_a: str,
        user_b: str,
        match_type: str,
        application_id: Optional[str] = None,
    ) -> Dict:
        """
        After mutual accept (user_a, user_b): create or merge cliques, create pod if size >= 3.
        Scoped by application_id so each application gets its own chat (clique/pod).
        Returns { clique, pod? }. Handles duplicate adds (e.g. X and Y both match Z - Z only added once).
        """
        cliques_a = self.clique_model.find_by_member(user_a, application_id=application_id)
        cliques_b = self.clique_model.find_by_member(user_b, application_id=application_id)
        existing_both = self.clique_model.find_containing_both(
            user_a, user_b, application_id=application_id
        )
        if existing_both:
            return {"clique": existing_both, "pod": self._pod_for_clique(existing_both, application_id)}

        # One clique contains both → already in same clique
        for c in cliques_a:
            if user_b in c.get("members", []):
                return {"clique": c, "pod": self._pod_for_clique(c, application_id)}

        # Find cliques containing only A or only B (already scoped by application_id above)
        only_a = [c for c in cliques_a if user_b not in (c.get("members") or [])]
        only_b = [c for c in cliques_b if user_a not in (c.get("members") or [])]

        if only_a and only_b and only_a[0]["_id"] != only_b[0]["_id"]:
            # Merge two cliques
            target = only_a[0]
            source = only_b[0]
            source_members = set(source.get("members") or [])
            target_members = set(target.get("members") or [])
            self.clique_model.merge_into(target["_id"], source["_id"])
            merged = self.clique_model.find_by_id(target["_id"])
            pod = self._pod_for_clique(merged, application_id)
            # If target had a pod, add any new members from source that aren't in the pod yet
            if pod:
                pod_members = set(pod.get("members") or [])
                for uid in source_members:
                    if uid not in target_members and uid not in pod_members:
                        try:
                            self.pod_service.add_member_to_pod(pod["_id"], uid)
                        except Exception:
                            pass
                pod = self.pod_service.pod_model.find_by_id(pod["_id"])
            return {"clique": merged, "pod": pod}

        if only_a:
            # Add user_b to clique containing user_a (if not already)
            c = only_a[0]
            if user_b not in (c.get("members") or []):
                self.clique_model.add_member(c["_id"], user_b)
            updated = self.clique_model.find_by_id(c["_id"])
            pod = self._pod_for_clique(updated, application_id)
            if pod and user_b not in (pod.get("members") or []):
                self.pod_service.add_member_to_pod(pod["_id"], user_b)
                pod = self.pod_service.pod_model.find_by_id(pod["_id"])
            return {"clique": updated, "pod": pod}

        if only_b:
            # Add user_a to clique containing user_b
            c = only_b[0]
            if user_a not in (c.get("members") or []):
                self.clique_model.add_member(c["_id"], user_a)
            updated = self.clique_model.find_by_id(c["_id"])
            pod = self._pod_for_clique(updated, application_id)
            if pod and user_a not in (pod.get("members") or []):
                self.pod_service.add_member_to_pod(pod["_id"], user_a)
                pod = self.pod_service.pod_model.find_by_id(pod["_id"])
            return {"clique": updated, "pod": pod}

        # New clique of 2 (for this application)
        clique_id = self.clique_model.create(
            [user_a, user_b],
            match_type=match_type,
            application_id=application_id,
        )
        clique = self.clique_model.find_by_id(clique_id)
        return {"clique": clique, "pod": self._pod_for_clique(clique, application_id)}

    def _pod_for_clique(
        self,
        clique: dict,
        application_id: Optional[str] = None,
    ) -> Optional[dict]:
        """If clique has 3+ members and no pod_id, create pod and set pod_id. Return pod if chatable."""
        members = clique.get("members") or []
        if len(members) < 3:
            return None
        pod_id = clique.get("pod_id")
        if pod_id:
            return self.pod_service.pod_model.find_by_id(pod_id)
        # Use application_id from clique if not passed (e.g. from merged clique)
        app_id = application_id or clique.get("application_id")
        # Create pod for this clique (one chat per application)
        pod = self.pod_service.create_pod(
            user_id=members[0],
            match_type=clique.get("match_type", "evolve"),
            member_ids=members,
            application_id=app_id,
        )
        self.clique_model.set_pod_id(clique["_id"], pod["_id"])
        return pod

    def accept_invitation(self, invitation_id: str, invitee_id: str) -> Dict:
        """
        Accept an invitation. Two flows:
        - Legacy: 2 invitations in same group, both accepted → pod of 3 (inviter + 2 invitees).
        - New: single invitation (inviter→invitee) → mutual accept → clique; if clique >= 3, create pod.
        Returns { accepted: True, pod?: ..., clique?: ... }
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
        accepted = [g for g in group if g.get("status") == "accepted"]

        # Legacy: 2 invitations in group (inviter invited 2 people)
        if len(group) == 2 and len(accepted) == 2:
            inviter_id = inv["inviter_id"]
            invitee_ids = [g["invitee_id"] for g in group]
            member_ids = [inviter_id] + invitee_ids
            pod = self.pod_service.create_pod(
                user_id=inviter_id,
                match_type=inv["match_type"],
                member_ids=member_ids,
                application_id=inv.get("application_id"),
            )
            return {"accepted": True, "pod": pod, "clique": None}

        # New: single invitation = mutual accept → clique (scoped by application for separate chats)
        inviter_id = inv["inviter_id"]
        application_id = inv.get("application_id")
        result = self._ensure_clique_and_pod(
            inviter_id, invitee_id, inv["match_type"], application_id=application_id
        )
        return {"accepted": True, "pod": result.get("pod"), "clique": result.get("clique")}

    def reject_invitation(self, invitation_id: str, invitee_id: str) -> None:
        """Reject an invitation. Cancel other pending in same group (legacy 2-invitee flow)."""
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
        self.invitation_model.cancel_group(inv["clique_group_id"])

    def add_member_to_clique_from_mutual(self, clique_id: str, new_member_id: str) -> Dict:
        """
        When a new mutual accept adds someone to an existing clique (e.g. Z with X or Y).
        Prevents adding twice: only add if not already in clique. Then ensure pod has them.
        """
        clique = self.clique_model.find_by_id(clique_id)
        if not clique:
            raise ValueError("Clique not found")
        members = clique.get("members") or []
        if new_member_id in members:
            return {"clique": clique, "pod": self._pod_for_clique(clique, clique.get("application_id"))}
        if len(members) >= MAX_CLIQUE_MEMBERS:
            raise ValueError(f"Clique already has maximum {MAX_CLIQUE_MEMBERS} members")
        self.clique_model.add_member(clique_id, new_member_id)
        updated = self.clique_model.find_by_id(clique_id)
        pod = self._pod_for_clique(updated, updated.get("application_id"))
        if pod and new_member_id not in (pod.get("members") or []):
            self.pod_service.add_member_to_pod(pod["_id"], new_member_id)
            updated_pod = self.pod_service.pod_model.find_by_id(pod["_id"])
            return {"clique": updated, "pod": updated_pod}
        return {"clique": updated, "pod": pod}
