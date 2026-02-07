"""Example usage of the matching service."""
# This is an example file showing how to use the matching service
# Note: This requires a running MongoDB instance and valid GEMINI_API_KEY

from backend.services.matching_service import MatchingService
from backend.models.user import User
from backend.models.pod import Pod

# Example: Finding matches for a user
def example_find_matches():
    """Example of finding matches for a user."""
    # Initialize the matching service
    matching_service = MatchingService()
    
    # Find matches for a user
    matches = matching_service.find_matches(
        user_id="user_id_here",
        match_type="friendship",  # or "goal" or "issues"
        focus_text="Looking for friends who love coding and AI"
    )
    
    # Process results
    for match in matches:
        print(f"User: {match['username']}")
        print(f"Similarity Score: {match['similarity_score']:.4f}")
        print(f"Focus: {match['matching_preferences']['current_focus_text']}")
        print("---")


# Example: Creating a user and setting up matching preferences
def example_create_user():
    """Example of creating a user with matching preferences."""
    user_model = User()
    
    user_data = {
        "username": "johndoe",
        "email": "john@example.com",
        "password_hash": "hashed_password_here",
        "profile": {
            "interests": ["coding", "AI", "machine learning"],
            "work_area": "Software Engineering",
            "current_goals": ["Learn Python", "Build AI projects"],
            "struggles": []
        },
        "matching_preferences": {
            "match_type": "friendship",
            "current_focus_text": "",
            "focus_embedding": None
        }
    }
    
    user_id = user_model.create(user_data)
    print(f"Created user with ID: {user_id}")
    return user_id


# Example: Creating a pod from matches
def example_create_pod():
    """Example of creating a pod from matched users."""
    pod_model = Pod()
    
    # After finding matches, create a pod with top 3 matches
    pod_id = pod_model.create(
        pod_type="friendship",
        member_ids=["user1_id", "user2_id", "user3_id"],
        gemini_icebreaker="You all share a passion for technology and coding!",
        focus_context="All members are interested in coding and AI"
    )
    
    print(f"Created pod with ID: {pod_id}")
    return pod_id


if __name__ == "__main__":
    print("This is an example usage file.")
    print("Make sure you have:")
    print("1. MongoDB running and MONGODB_URI set in .env")
    print("2. GEMINI_API_KEY set in .env")
    print("3. All dependencies installed (pip install -r requirements.txt)")

