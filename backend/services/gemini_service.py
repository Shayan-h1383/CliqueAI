"""Gemini API service for embeddings and icebreaker generation."""
import os
from typing import List, Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class GeminiService:
    """Service for interacting with Google's Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Gemini API key. If not provided, reads from GEMINI_API_KEY env var.
            
        Raises:
            ValueError: If API key is not provided and not found in environment
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please set it in your .env file or pass it as a parameter."
            )
        
        genai.configure(api_key=self.api_key)
        
        # Initialize models
        # embedding-001 was deprecated; use gemini-embedding-001
        self.embedding_model = "models/gemini-embedding-001"
        self.chat_model = "gemini-1.5-pro"
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for given text using Gemini embedding model.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List[float]: Embedding vector (768 dimensions for embedding-001)
            
        Raises:
            Exception: If API call fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                output_dimensionality=768  # Match schema; 3072 is default for gemini-embedding-001
            )
            
            embedding = result['embedding']
            return embedding
            
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}") from e
    
    def generate_icebreaker(
        self,
        user_profiles: List[Dict],
        match_type: str
    ) -> str:
        """
        Generate an icebreaker message explaining why users should talk.
        
        Args:
            user_profiles: List of user profile dictionaries containing:
                - username
                - profile (interests, work_area, current_goals, struggles)
                - matching_preferences (current_focus_text)
            match_type: Type of match ("friendship", "goal", or "issues")
            
        Returns:
            str: Generated icebreaker text
            
        Raises:
            ValueError: If user_profiles is empty or match_type is invalid
            Exception: If API call fails
        """
        if not user_profiles:
            raise ValueError("user_profiles cannot be empty")
        
        if match_type not in ['friendship', 'goal', 'issues']:
            raise ValueError("match_type must be one of: friendship, goal, issues")
        
        # Build context from user profiles
        context_parts = []
        for i, profile in enumerate(user_profiles, 1):
            username = profile.get('username', f'User {i}')
            user_profile = profile.get('profile', {})
            focus_text = profile.get('matching_preferences', {}).get('current_focus_text', '')
            
            context = f"User {i} ({username}):\n"
            if focus_text:
                context += f"Current focus: {focus_text}\n"
            
            if match_type == 'friendship':
                interests = user_profile.get('interests', [])
                if interests:
                    context += f"Interests: {', '.join(interests)}\n"
            elif match_type == 'goal':
                work_area = user_profile.get('work_area')
                goals = user_profile.get('current_goals', [])
                if work_area:
                    context += f"Work area: {work_area}\n"
                if goals:
                    context += f"Current goals: {', '.join(goals)}\n"
            elif match_type == 'issues':
                struggles = user_profile.get('struggles', [])
                if struggles:
                    context += f"Struggles: {', '.join(struggles)}\n"
            
            context_parts.append(context)
        
        user_context = "\n".join(context_parts)
        
        # Create prompt
        prompt = f"""Explain why these {len(user_profiles)} people should talk based on their shared {match_type} connection. Be warm, specific, and create psychological safety. Focus on what they have in common and why this conversation could be meaningful.

User information:
{user_context}

Generate a warm, encouraging icebreaker that helps them feel comfortable starting a conversation."""

        try:
            model = genai.GenerativeModel(self.chat_model)
            response = model.generate_content(prompt)
            
            icebreaker = response.text.strip()
            return icebreaker
            
        except Exception as e:
            raise Exception(f"Failed to generate icebreaker: {str(e)}") from e

