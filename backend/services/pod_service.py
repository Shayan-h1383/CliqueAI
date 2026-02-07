"""Pod service for pod creation, management, and expiration handling."""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bson import ObjectId

from backend.models.pod import Pod, MAX_POD_MEMBERS
from backend.models.user import User
from backend.services.gemini_service import GeminiService


class PodService:
    """Service for pod operations."""
    
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        """
        Initialize PodService.
        
        Args:
            gemini_service: Optional GeminiService instance. If not provided, creates a new one.
        """
        self.pod_model = Pod()
        self.user_model = User()
        self.gemini_service = gemini_service or GeminiService()
    
    def create_pod(
        self,
        user_id: str,
        match_type: str,
        member_ids: List[str]
    ) -> Dict:
        """
        Create a new pod with 3-10 members.
        
        Args:
            user_id: ID of the user creating the pod (must be in member_ids)
            match_type: Type of pod (evolve, enjoy, support)
            member_ids: List of 3-10 user IDs including the requester
            
        Returns:
            dict: Created pod with icebreaker
            
        Raises:
            ValueError: If validation fails
        """
        # Validate 3-10 members
        if len(member_ids) < 3 or len(member_ids) > MAX_POD_MEMBERS:
            raise ValueError(f"Pod must have between 3 and {MAX_POD_MEMBERS} members")
        
        # Validate requester is in member list
        if user_id not in member_ids:
            raise ValueError("Requester must be included in member_ids")
        
        # Validate match_type
        if match_type not in ['evolve', 'enjoy', 'support']:
            raise ValueError("match_type must be one of: evolve, enjoy, support")
        
        # Check all members exist (allow multiple cliques per user)
        user_profiles = []
        for member_id in member_ids:
            user = self.user_model.find_by_id(member_id)
            if not user:
                raise ValueError(f"User {member_id} not found")
            
            # Collect user profile for icebreaker generation
            user_profiles.append({
                'username': user.get('username', 'Unknown'),
                'profile': user.get('profile', {}),
                'matching_preferences': user.get('matching_preferences', {})
            })
        
        # Aggregate focus_text from all members
        focus_contexts = []
        for user in user_profiles:
            focus_text = user.get('matching_preferences', {}).get('current_focus_text')
            if focus_text:
                focus_contexts.append(focus_text)
        
        focus_context = ' | '.join(focus_contexts) if focus_contexts else None
        
        # Generate icebreaker using Gemini; fallback so pod is always created
        icebreaker = None
        try:
            icebreaker = self.gemini_service.generate_icebreaker(
                user_profiles=user_profiles,
                match_type=match_type
            )
        except Exception as e:
            usernames = [p.get("username", "Someone") for p in user_profiles]
            icebreaker = (
                f"You're all connected. Say hi and share what brought you here — "
                f"{', '.join(usernames[:3])}{' and others' if len(usernames) > 3 else ''}."
            )
        
        # Create pod
        pod_id = self.pod_model.create(
            pod_type=match_type,
            member_ids=member_ids,
            gemini_icebreaker=icebreaker,
            focus_context=focus_context
        )
        
        # Update all members' active_pod_id
        for member_id in member_ids:
            self.user_model.set_active_pod(member_id, pod_id)
        
        # Fetch and return created pod
        pod = self.pod_model.find_by_id(pod_id)
        if not pod:
            raise ValueError("Failed to create pod")
        
        return pod

    def add_member_to_pod(self, pod_id: str, user_id: str) -> bool:
        """
        Add a member to an existing pod (e.g. when clique grows).
        Sets the new member's active_pod_id. Returns True if added.
        """
        pod = self.pod_model.find_by_id(pod_id)
        if not pod:
            raise ValueError("Pod not found")
        if user_id in pod.get("members", []):
            return False
        if len(pod.get("members", [])) >= MAX_POD_MEMBERS:
            raise ValueError(f"Pod already has maximum {MAX_POD_MEMBERS} members")
        user = self.user_model.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        ok = self.pod_model.add_member(pod_id, user_id)
        if ok:
            self.user_model.set_active_pod(user_id, pod_id)
        return ok

    def leave_pod(self, user_id: str, pod_id: str) -> bool:
        """
        Remove a user from a pod.
        
        Args:
            user_id: ID of the user leaving
            pod_id: ID of the pod to leave
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If user is not a member of the pod
        """
        # Get pod
        pod = self.pod_model.find_by_id(pod_id)
        if not pod:
            raise ValueError("Pod not found")
        
        # Check if user is a member
        if user_id not in pod.get('members', []):
            raise ValueError("User is not a member of this pod")
        
        # Remove user from pod members
        updated_members = [mid for mid in pod['members'] if mid != user_id]
        
        # Update pod
        update_data = {'members': updated_members}
        
        # If pod becomes empty or has less than 2 members, deactivate it
        if len(updated_members) < 2:
            update_data['is_active'] = False
        
        self.pod_model.update(pod_id, update_data)
        
        # Clear user's active_pod_id
        self.user_model.set_active_pod(user_id, None)
        
        return True
    
    def expire_pods(self) -> int:
        """
        Deactivate all expired pods and clear active_pod_id for their members.
        
        Returns:
            int: Number of pods deactivated
        """
        # Deactivate expired pods
        count = self.pod_model.deactivate_expired()
        
        # Find all expired pods that are now inactive
        # and clear active_pod_id for their members
        expired_pods = self.pod_model.collection.find({
            'is_active': False,
            'expires_at': {'$lt': datetime.utcnow()}
        })
        
        for pod in expired_pods:
            member_ids = [str(mid) for mid in pod.get('members', [])]
            for member_id in member_ids:
                # Only clear if this pod is still their active pod
                user = self.user_model.find_by_id(member_id)
                if user and user.get('active_pod_id') == str(pod['_id']):
                    self.user_model.set_active_pod(member_id, None)
        
        return count
    
    def is_pod_expired(self, pod_id: str) -> bool:
        """
        Check if a pod has expired.
        
        Args:
            pod_id: ID of the pod to check
            
        Returns:
            bool: True if pod is expired
        """
        pod = self.pod_model.find_by_id(pod_id)
        if not pod:
            return True
        
        expires_at = pod.get('expires_at')
        if not expires_at:
            return True
        
        # Convert string to datetime if needed
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        
        return expires_at < datetime.utcnow()

