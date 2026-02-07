"""Matching service for finding semantically similar users."""
from typing import List, Dict, Optional
from datetime import datetime

from backend.models.user import User
from backend.services.gemini_service import GeminiService
from backend.utils.embeddings import cosine_similarity


class MatchingService:
    """Service for finding matches based on semantic similarity."""
    
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        """
        Initialize matching service.
        
        Args:
            gemini_service: Optional GeminiService instance. If not provided, creates a new one.
        """
        self.gemini_service = gemini_service or GeminiService()
        self.user_model = User()
    
    def find_matches(
        self,
        user_id: str,
        match_type: str,
        focus_text: str
    ) -> List[Dict]:
        """
        Find top 4 matches for a user based on semantic similarity.
        
        Args:
            user_id: ID of the user looking for matches
            match_type: Type of match ("friendship", "goal", or "issues")
            focus_text: User's input describing their current need
            
        Returns:
            List[Dict]: List of match dictionaries, each containing:
                - user_id: Matched user's ID
                - username: Matched user's username
                - similarity_score: Cosine similarity score (0-1)
                - profile: User's profile information
                Sorted by similarity score (descending), max 4 results.
                
        Raises:
            ValueError: If user_id is invalid, match_type is invalid, or focus_text is empty
            Exception: If embedding generation or database operations fail
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")
        
        if match_type not in ['friendship', 'goal', 'issues']:
            raise ValueError("match_type must be one of: friendship, goal, issues")
        
        if not focus_text or not focus_text.strip():
            raise ValueError("focus_text cannot be empty")
        
        # Get or verify user exists
        user = self.user_model.find_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Generate embedding for focus_text
        try:
            embedding = self.gemini_service.get_embedding(focus_text)
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}") from e
        
        # Store embedding in user's matching preferences
        self.user_model.update_matching_preferences(
            user_id=user_id,
            match_type=match_type,
            current_focus_text=focus_text,
            focus_embedding=embedding
        )
        
        # Find candidate users
        candidates = self.user_model.find_candidates_for_matching(
            match_type=match_type,
            exclude_user_id=user_id,
            has_embedding=True
        )
        
        if not candidates:
            return []
        
        # Calculate similarity scores
        matches_with_scores = []
        for candidate in candidates:
            candidate_embedding = candidate.get('matching_preferences', {}).get('focus_embedding')
            
            if not candidate_embedding:
                continue
            
            try:
                similarity = cosine_similarity(embedding, candidate_embedding)
                
                matches_with_scores.append({
                    'user_id': candidate['_id'],
                    'username': candidate.get('username', 'Unknown'),
                    'similarity_score': float(similarity),
                    'profile': candidate.get('profile', {}),
                    'matching_preferences': {
                        'current_focus_text': candidate.get('matching_preferences', {}).get('current_focus_text')
                    }
                })
            except Exception as e:
                # Skip candidates with invalid embeddings
                continue
        
        # Sort by similarity score (descending)
        matches_with_scores.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Return top 4 matches
        return matches_with_scores[:4]
    
    def find_matches_with_existing_embedding(
        self,
        user_id: str,
        match_type: str
    ) -> List[Dict]:
        """
        Find matches using user's existing embedding (if available).
        
        This is useful when the user's focus hasn't changed and we want to
        avoid regenerating the embedding.
        
        Args:
            user_id: ID of the user looking for matches
            match_type: Type of match ("friendship", "goal", or "issues")
            
        Returns:
            List[Dict]: List of match dictionaries (same format as find_matches)
            
        Raises:
            ValueError: If user has no existing embedding or match_type doesn't match
        """
        user = self.user_model.find_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        matching_prefs = user.get('matching_preferences', {})
        user_match_type = matching_prefs.get('match_type')
        embedding = matching_prefs.get('focus_embedding')
        
        if not embedding:
            raise ValueError(f"User {user_id} has no existing embedding. Use find_matches() instead.")
        
        if user_match_type != match_type:
            raise ValueError(
                f"User's match_type ({user_match_type}) doesn't match requested type ({match_type}). "
                "Use find_matches() to update."
            )
        
        # Find candidate users
        candidates = self.user_model.find_candidates_for_matching(
            match_type=match_type,
            exclude_user_id=user_id,
            has_embedding=True
        )
        
        if not candidates:
            return []
        
        # Calculate similarity scores
        matches_with_scores = []
        for candidate in candidates:
            candidate_embedding = candidate.get('matching_preferences', {}).get('focus_embedding')
            
            if not candidate_embedding:
                continue
            
            try:
                similarity = cosine_similarity(embedding, candidate_embedding)
                
                matches_with_scores.append({
                    'user_id': candidate['_id'],
                    'username': candidate.get('username', 'Unknown'),
                    'similarity_score': float(similarity),
                    'profile': candidate.get('profile', {}),
                    'matching_preferences': {
                        'current_focus_text': candidate.get('matching_preferences', {}).get('current_focus_text')
                    }
                })
            except Exception as e:
                continue
        
        # Sort by similarity score (descending)
        matches_with_scores.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Return top 4 matches
        return matches_with_scores[:4]

