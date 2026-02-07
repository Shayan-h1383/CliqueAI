"""Tests for embedding utilities and Gemini service."""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from backend.utils.embeddings import cosine_similarity, normalize_vector
from backend.services.gemini_service import GeminiService


class TestCosineSimilarity:
    """Tests for cosine similarity function."""
    
    def test_identical_vectors(self):
        """Test that identical vectors have similarity of 1.0."""
        vec = [1.0, 2.0, 3.0, 4.0]
        result = cosine_similarity(vec, vec)
        assert result == pytest.approx(1.0, abs=1e-6)
    
    def test_orthogonal_vectors(self):
        """Test that orthogonal vectors have similarity of 0.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        result = cosine_similarity(vec1, vec2)
        assert result == pytest.approx(0.0, abs=1e-6)
    
    def test_opposite_vectors(self):
        """Test that opposite vectors have similarity of -1.0."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]
        result = cosine_similarity(vec1, vec2)
        assert result == pytest.approx(-1.0, abs=1e-6)
    
    def test_different_length_vectors(self):
        """Test that vectors of different lengths raise ValueError."""
        vec1 = [1.0, 2.0]
        vec2 = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError, match="same length"):
            cosine_similarity(vec1, vec2)
    
    def test_empty_vectors(self):
        """Test that empty vectors raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            cosine_similarity([], [])
    
    def test_zero_vector(self):
        """Test that zero vectors return 0.0 similarity."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]
        result = cosine_similarity(vec1, vec2)
        assert result == 0.0
    
    def test_known_similarity(self):
        """Test with known vectors and expected similarity."""
        # Unit vectors at 45 degrees
        vec1 = [1.0, 0.0]
        vec2 = [1.0, 1.0]  # Normalized: [1/sqrt(2), 1/sqrt(2)]
        # Dot product: 1*1 + 0*1 = 1
        # Norm vec1: 1, Norm vec2: sqrt(2)
        # Similarity: 1 / (1 * sqrt(2)) = 1/sqrt(2) ≈ 0.707
        result = cosine_similarity(vec1, vec2)
        expected = 1.0 / np.sqrt(2.0)
        assert result == pytest.approx(expected, abs=1e-6)
    
    def test_high_dimensional_vectors(self):
        """Test with high-dimensional vectors (like embeddings)."""
        vec1 = [0.1] * 768
        vec2 = [0.2] * 768
        result = cosine_similarity(vec1, vec2)
        # Identical direction, should be 1.0
        assert result == pytest.approx(1.0, abs=1e-6)


class TestNormalizeVector:
    """Tests for vector normalization function."""
    
    def test_normalize_unit_vector(self):
        """Test that normalized unit vector has norm 1."""
        vec = [3.0, 4.0, 0.0]
        normalized = normalize_vector(vec)
        norm = np.linalg.norm(normalized)
        assert norm == pytest.approx(1.0, abs=1e-6)
    
    def test_normalize_preserves_direction(self):
        """Test that normalization preserves direction."""
        vec = [1.0, 2.0, 3.0]
        normalized = normalize_vector(vec)
        # Check that normalized is in same direction (proportional)
        ratio = normalized[0] / vec[0]
        assert normalized[1] / vec[1] == pytest.approx(ratio, abs=1e-6)
        assert normalized[2] / vec[2] == pytest.approx(ratio, abs=1e-6)
    
    def test_normalize_zero_vector(self):
        """Test that zero vector raises ValueError."""
        with pytest.raises(ValueError, match="zero vector"):
            normalize_vector([0.0, 0.0, 0.0])
    
    def test_normalize_empty_vector(self):
        """Test that empty vector raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            normalize_vector([])


class TestGeminiService:
    """Tests for Gemini service with mocked API calls."""
    
    @patch('backend.services.gemini_service.genai')
    def test_get_embedding_success(self, mock_genai):
        """Test successful embedding generation."""
        # Setup mock
        mock_embedding = [0.1] * 768
        mock_genai.embed_content.return_value = {'embedding': mock_embedding}
        
        service = GeminiService(api_key='test_key')
        result = service.get_embedding("test text")
        
        assert result == mock_embedding
        mock_genai.embed_content.assert_called_once()
    
    @patch('backend.services.gemini_service.genai')
    def test_get_embedding_empty_text(self, mock_genai):
        """Test that empty text raises ValueError."""
        service = GeminiService(api_key='test_key')
        
        with pytest.raises(ValueError, match="cannot be empty"):
            service.get_embedding("")
        
        with pytest.raises(ValueError, match="cannot be empty"):
            service.get_embedding("   ")
    
    @patch('backend.services.gemini_service.genai')
    def test_get_embedding_api_error(self, mock_genai):
        """Test handling of API errors."""
        mock_genai.embed_content.side_effect = Exception("API Error")
        
        service = GeminiService(api_key='test_key')
        
        with pytest.raises(Exception, match="Failed to generate embedding"):
            service.get_embedding("test text")
    
    @patch('backend.services.gemini_service.genai')
    def test_generate_icebreaker_success(self, mock_genai):
        """Test successful icebreaker generation."""
        # Setup mock
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "You all share a passion for technology!"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        service = GeminiService(api_key='test_key')
        
        user_profiles = [
            {
                'username': 'user1',
                'profile': {'interests': ['coding', 'AI']},
                'matching_preferences': {'current_focus_text': 'Looking for coding buddies'}
            },
            {
                'username': 'user2',
                'profile': {'interests': ['coding', 'ML']},
                'matching_preferences': {'current_focus_text': 'Want to learn ML'}
            }
        ]
        
        result = service.generate_icebreaker(user_profiles, 'friendship')
        
        assert result == "You all share a passion for technology!"
        mock_model.generate_content.assert_called_once()
    
    @patch('backend.services.gemini_service.genai')
    def test_generate_icebreaker_empty_profiles(self, mock_genai):
        """Test that empty profiles raise ValueError."""
        service = GeminiService(api_key='test_key')
        
        with pytest.raises(ValueError, match="cannot be empty"):
            service.generate_icebreaker([], 'friendship')
    
    @patch('backend.services.gemini_service.genai')
    def test_generate_icebreaker_invalid_match_type(self, mock_genai):
        """Test that invalid match_type raises ValueError."""
        service = GeminiService(api_key='test_key')
        
        with pytest.raises(ValueError, match="must be one of"):
            service.generate_icebreaker([{'username': 'user1'}], 'invalid')
    
    def test_gemini_service_missing_api_key(self):
        """Test that missing API key raises ValueError."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                GeminiService()

