"""Tests for matching algorithm."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from bson import ObjectId

from backend.services.matching_service import MatchingService
from backend.services.gemini_service import GeminiService
from backend.models.user import User


class TestMatchingService:
    """Tests for matching service."""
    
    @pytest.fixture
    def mock_gemini_service(self):
        """Create a mock Gemini service."""
        service = MagicMock(spec=GeminiService)
        service.get_embedding.return_value = [0.1] * 768
        return service
    
    @pytest.fixture
    def mock_user_model(self):
        """Create a mock User model."""
        with patch('backend.services.matching_service.User') as mock_user_class:
            user_model = MagicMock()
            mock_user_class.return_value = user_model
            yield user_model
    
    def test_find_matches_success(self, mock_gemini_service, mock_user_model):
        """Test successful matching with 4+ candidates."""
        # Setup user
        user_id = str(ObjectId())
        mock_user_model.find_by_id.return_value = {
            "_id": user_id,
            "username": "user1",
            "matching_preferences": {}
        }
        
        # Setup candidates
        candidates = []
        for i in range(5):
            candidate_id = str(ObjectId())
            candidates.append({
                "_id": candidate_id,
                "username": f"candidate{i}",
                "profile": {"interests": [f"interest{i}"]},
                "matching_preferences": {
                    "focus_embedding": [0.1 + i * 0.01] * 768,
                    "current_focus_text": f"Focus {i}"
                }
            })
        
        mock_user_model.find_candidates_for_matching.return_value = candidates
        mock_user_model.update_matching_preferences.return_value = True
        
        # Create matching service
        matching_service = MatchingService(gemini_service=mock_gemini_service)
        matching_service.user_model = mock_user_model
        
        # Test
        matches = matching_service.find_matches(
            user_id=user_id,
            match_type="friendship",
            focus_text="Looking for friends"
        )
        
        # Verify
        assert len(matches) == 4  # Top 4
        assert all("user_id" in m for m in matches)
        assert all("similarity_score" in m for m in matches)
        assert all("username" in m for m in matches)
        assert all(m["similarity_score"] >= 0 for m in matches)
        
        # Verify scores are sorted descending
        scores = [m["similarity_score"] for m in matches]
        assert scores == sorted(scores, reverse=True)
        
        # Verify embedding was generated
        mock_gemini_service.get_embedding.assert_called_once_with("Looking for friends")
        
        # Verify preferences were updated
        mock_user_model.update_matching_preferences.assert_called_once()
    
    def test_find_matches_less_than_4(self, mock_gemini_service, mock_user_model):
        """Test matching when less than 4 candidates available."""
        user_id = str(ObjectId())
        mock_user_model.find_by_id.return_value = {
            "_id": user_id,
            "username": "user1"
        }
        
        # Only 2 candidates
        candidates = []
        for i in range(2):
            candidates.append({
                "_id": str(ObjectId()),
                "username": f"candidate{i}",
                "profile": {},
                "matching_preferences": {
                    "focus_embedding": [0.1 + i * 0.01] * 768,
                    "current_focus_text": f"Focus {i}"
                }
            })
        
        mock_user_model.find_candidates_for_matching.return_value = candidates
        mock_user_model.update_matching_preferences.return_value = True
        
        matching_service = MatchingService(gemini_service=mock_gemini_service)
        matching_service.user_model = mock_user_model
        
        matches = matching_service.find_matches(
            user_id=user_id,
            match_type="goal",
            focus_text="Want to learn Python"
        )
        
        assert len(matches) == 2
        assert all("similarity_score" in m for m in matches)
    
    def test_find_matches_no_candidates(self, mock_gemini_service, mock_user_model):
        """Test matching when no candidates found."""
        user_id = str(ObjectId())
        mock_user_model.find_by_id.return_value = {
            "_id": user_id,
            "username": "user1"
        }
        mock_user_model.find_candidates_for_matching.return_value = []
        mock_user_model.update_matching_preferences.return_value = True
        
        matching_service = MatchingService(gemini_service=mock_gemini_service)
        matching_service.user_model = mock_user_model
        
        matches = matching_service.find_matches(
            user_id=user_id,
            match_type="issues",
            focus_text="Struggling with anxiety"
        )
        
        assert len(matches) == 0
    
    def test_find_matches_invalid_user_id(self, mock_gemini_service, mock_user_model):
        """Test matching with invalid user ID."""
        mock_user_model.find_by_id.return_value = None
        
        matching_service = MatchingService(gemini_service=mock_gemini_service)
        matching_service.user_model = mock_user_model
        
        with pytest.raises(ValueError, match="not found"):
            matching_service.find_matches(
                user_id="invalid_id",
                match_type="friendship",
                focus_text="Test"
            )
    
    def test_find_matches_invalid_match_type(self, mock_gemini_service, mock_user_model):
        """Test matching with invalid match type."""
        matching_service = MatchingService(gemini_service=mock_gemini_service)
        
        with pytest.raises(ValueError, match="must be one of"):
            matching_service.find_matches(
                user_id=str(ObjectId()),
                match_type="invalid_type",
                focus_text="Test"
            )
    
    def test_find_matches_empty_focus_text(self, mock_gemini_service, mock_user_model):
        """Test matching with empty focus text."""
        matching_service = MatchingService(gemini_service=mock_gemini_service)
        
        with pytest.raises(ValueError, match="cannot be empty"):
            matching_service.find_matches(
                user_id=str(ObjectId()),
                match_type="friendship",
                focus_text=""
            )
        
        with pytest.raises(ValueError, match="cannot be empty"):
            matching_service.find_matches(
                user_id=str(ObjectId()),
                match_type="friendship",
                focus_text="   "
            )
    
    def test_find_matches_embedding_generation_failure(self, mock_gemini_service, mock_user_model):
        """Test handling of embedding generation failure."""
        user_id = str(ObjectId())
        mock_user_model.find_by_id.return_value = {
            "_id": user_id,
            "username": "user1"
        }
        mock_gemini_service.get_embedding.side_effect = Exception("API Error")
        
        matching_service = MatchingService(gemini_service=mock_gemini_service)
        matching_service.user_model = mock_user_model
        
        with pytest.raises(Exception, match="Failed to generate embedding"):
            matching_service.find_matches(
                user_id=user_id,
                match_type="friendship",
                focus_text="Test"
            )
    
    def test_find_matches_candidate_without_embedding(self, mock_gemini_service, mock_user_model):
        """Test that candidates without embeddings are skipped."""
        user_id = str(ObjectId())
        mock_user_model.find_by_id.return_value = {
            "_id": user_id,
            "username": "user1"
        }
        
        # Mix of candidates with and without embeddings
        candidates = [
            {
                "_id": str(ObjectId()),
                "username": "candidate1",
                "profile": {},
                "matching_preferences": {
                    "focus_embedding": [0.1] * 768,
                    "current_focus_text": "Focus 1"
                }
            },
            {
                "_id": str(ObjectId()),
                "username": "candidate2",
                "profile": {},
                "matching_preferences": {
                    "focus_embedding": None,  # No embedding
                    "current_focus_text": "Focus 2"
                }
            },
            {
                "_id": str(ObjectId()),
                "username": "candidate3",
                "profile": {},
                "matching_preferences": {
                    "focus_embedding": [0.2] * 768,
                    "current_focus_text": "Focus 3"
                }
            }
        ]
        
        mock_user_model.find_candidates_for_matching.return_value = candidates
        mock_user_model.update_matching_preferences.return_value = True
        
        matching_service = MatchingService(gemini_service=mock_gemini_service)
        matching_service.user_model = mock_user_model
        
        matches = matching_service.find_matches(
            user_id=user_id,
            match_type="friendship",
            focus_text="Test"
        )
        
        # Should only return candidates with embeddings
        assert len(matches) == 2
        assert all(m["username"] in ["candidate1", "candidate3"] for m in matches)
    
    def test_find_matches_with_existing_embedding_success(self, mock_gemini_service, mock_user_model):
        """Test finding matches using existing embedding."""
        user_id = str(ObjectId())
        existing_embedding = [0.1] * 768
        
        mock_user_model.find_by_id.return_value = {
            "_id": user_id,
            "username": "user1",
            "matching_preferences": {
                "match_type": "friendship",
                "focus_embedding": existing_embedding
            }
        }
        
        candidates = [
            {
                "_id": str(ObjectId()),
                "username": "candidate1",
                "profile": {},
                "matching_preferences": {
                    "focus_embedding": [0.15] * 768,
                    "current_focus_text": "Focus 1"
                }
            }
        ]
        
        mock_user_model.find_candidates_for_matching.return_value = candidates
        
        matching_service = MatchingService(gemini_service=mock_gemini_service)
        matching_service.user_model = mock_user_model
        
        matches = matching_service.find_matches_with_existing_embedding(
            user_id=user_id,
            match_type="friendship"
        )
        
        assert len(matches) == 1
        # Should not call get_embedding
        mock_gemini_service.get_embedding.assert_not_called()
    
    def test_find_matches_with_existing_embedding_no_embedding(self, mock_gemini_service, mock_user_model):
        """Test finding matches when user has no existing embedding."""
        user_id = str(ObjectId())
        mock_user_model.find_by_id.return_value = {
            "_id": user_id,
            "username": "user1",
            "matching_preferences": {
                "match_type": "friendship",
                "focus_embedding": None
            }
        }
        
        matching_service = MatchingService(gemini_service=mock_gemini_service)
        matching_service.user_model = mock_user_model
        
        with pytest.raises(ValueError, match="no existing embedding"):
            matching_service.find_matches_with_existing_embedding(
                user_id=user_id,
                match_type="friendship"
            )
    
    def test_find_matches_with_existing_embedding_mismatch_type(self, mock_gemini_service, mock_user_model):
        """Test finding matches when match_type doesn't match."""
        user_id = str(ObjectId())
        mock_user_model.find_by_id.return_value = {
            "_id": user_id,
            "username": "user1",
            "matching_preferences": {
                "match_type": "friendship",
                "focus_embedding": [0.1] * 768
            }
        }
        
        matching_service = MatchingService(gemini_service=mock_gemini_service)
        matching_service.user_model = mock_user_model
        
        with pytest.raises(ValueError, match="doesn't match"):
            matching_service.find_matches_with_existing_embedding(
                user_id=user_id,
                match_type="goal"
            )
    
    def test_find_matches_similarity_scores(self, mock_gemini_service, mock_user_model):
        """Test that similarity scores are calculated correctly."""
        user_id = str(ObjectId())
        user_embedding = [1.0, 0.0, 0.0]  # Unit vector in x direction
        
        mock_user_model.find_by_id.return_value = {
            "_id": user_id,
            "username": "user1"
        }
        
        # Create candidates with known similarity
        # Candidate 1: Same direction (should have similarity ~1.0)
        # Candidate 2: Perpendicular (should have similarity ~0.0)
        # Candidate 3: Opposite direction (should have similarity ~-1.0)
        
        # Note: We need to use 768-dim vectors for real embeddings
        # But for testing, we'll use shorter vectors and mock the embedding
        mock_gemini_service.get_embedding.return_value = user_embedding * 256  # 768 dims
        
        candidates = [
            {
                "_id": str(ObjectId()),
                "username": "candidate1",
                "profile": {},
                "matching_preferences": {
                    "focus_embedding": [1.0, 0.0, 0.0] * 256,  # Same direction
                    "current_focus_text": "Focus 1"
                }
            },
            {
                "_id": str(ObjectId()),
                "username": "candidate2",
                "profile": {},
                "matching_preferences": {
                    "focus_embedding": [0.0, 1.0, 0.0] * 256,  # Perpendicular
                    "current_focus_text": "Focus 2"
                }
            }
        ]
        
        mock_user_model.find_candidates_for_matching.return_value = candidates
        mock_user_model.update_matching_preferences.return_value = True
        
        matching_service = MatchingService(gemini_service=mock_gemini_service)
        matching_service.user_model = mock_user_model
        
        matches = matching_service.find_matches(
            user_id=user_id,
            match_type="friendship",
            focus_text="Test"
        )
        
        assert len(matches) == 2
        # First candidate should have higher similarity
        assert matches[0]["similarity_score"] > matches[1]["similarity_score"]
        # Scores should be valid (between -1 and 1)
        assert all(-1.0 <= m["similarity_score"] <= 1.0 for m in matches)

