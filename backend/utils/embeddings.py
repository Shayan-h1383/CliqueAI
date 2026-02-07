"""Utility functions for vector operations."""
import numpy as np
from typing import List


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Cosine similarity measures the cosine of the angle between two vectors,
    ranging from -1 (opposite) to 1 (identical), with 0 indicating orthogonality.
    
    Args:
        vec1: First vector as list of floats
        vec2: Second vector as list of floats
        
    Returns:
        float: Cosine similarity score between -1 and 1
        
    Raises:
        ValueError: If vectors have different lengths or are empty
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"Vectors must have the same length. Got {len(vec1)} and {len(vec2)}")
    
    if len(vec1) == 0:
        raise ValueError("Vectors cannot be empty")
    
    # Convert to numpy arrays
    a = np.array(vec1, dtype=np.float64)
    b = np.array(vec2, dtype=np.float64)
    
    # Calculate dot product
    dot_product = np.dot(a, b)
    
    # Calculate norms
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    # Handle zero vectors
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    # Calculate cosine similarity
    similarity = dot_product / (norm_a * norm_b)
    
    # Ensure result is within valid range (should be, but handle floating point errors)
    return float(np.clip(similarity, -1.0, 1.0))


def normalize_vector(vec: List[float]) -> List[float]:
    """
    Normalize a vector to unit length.
    
    Args:
        vec: Vector as list of floats
        
    Returns:
        List[float]: Normalized vector
        
    Raises:
        ValueError: If vector is empty or has zero norm
    """
    if len(vec) == 0:
        raise ValueError("Vector cannot be empty")
    
    a = np.array(vec, dtype=np.float64)
    norm = np.linalg.norm(a)
    
    if norm == 0:
        raise ValueError("Cannot normalize zero vector")
    
    normalized = a / norm
    return normalized.tolist()

