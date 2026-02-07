"""Pytest configuration and fixtures."""
import os
import pytest
from flask import Flask
from flask.testing import FlaskClient
from pymongo.errors import ConnectionFailure

# Set environment variables BEFORE importing app modules
# Use test database - requires MongoDB running (see README for setup)
os.environ.setdefault('MONGODB_URI', os.getenv('TEST_MONGODB_URI', 'mongodb://localhost:27017/hacketon_test'))
os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key-for-testing-only')
os.environ.setdefault('GEMINI_API_KEY', 'test-key')  # Mock key for tests

from backend.app import create_app
from backend.config.database import db_connection


def mongodb_available():
    """Check if MongoDB is running and accessible."""
    try:
        from backend.config.database import DatabaseConnection
        DatabaseConnection._instance = None
        DatabaseConnection._client = None
        DatabaseConnection._db = None
        db = db_connection.db
        return True
    except (ConnectionFailure, Exception):
        return False


@pytest.fixture(scope='function')
def app():
    """Create application for testing. Skips if MongoDB not available."""
    # Reset database connection singleton to use test database
    from backend.config.database import DatabaseConnection
    DatabaseConnection._instance = None
    DatabaseConnection._client = None
    DatabaseConnection._db = None
    
    # Ensure test database URI is set
    os.environ['MONGODB_URI'] = os.getenv('TEST_MONGODB_URI', 'mongodb://localhost:27017/hacketon_test')
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-testing-only'
    
    try:
        app = create_app()
    except ConnectionFailure:
        pytest.skip("MongoDB not running. Start MongoDB and run: python scripts/check_db.py")
    
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def client(app: Flask) -> FlaskClient:
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def test_db(app):
    """Set up and tear down test database. Skips if MongoDB not available."""
    if not mongodb_available():
        pytest.skip("MongoDB not running. Start MongoDB and run: python scripts/check_db.py")
    # Reset database connection to ensure we're using test database
    from backend.config.database import DatabaseConnection
    DatabaseConnection._instance = None
    DatabaseConnection._client = None
    DatabaseConnection._db = None
    
    # Clear test collections before each test
    db = db_connection.db
    db.users.delete_many({})
    db.pods.delete_many({})
    db.messages.delete_many({})
    
    yield db
    
    # Clean up after test
    db.users.delete_many({})
    db.pods.delete_many({})
    db.messages.delete_many({})


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpassword123'
    }


@pytest.fixture
def sample_user_data_2():
    """Second sample user data for testing."""
    return {
        'username': 'testuser2',
        'email': 'test2@example.com',
        'password': 'testpassword123'
    }


@pytest.fixture
def sample_user_data_3():
    """Third sample user data for testing."""
    return {
        'username': 'testuser3',
        'email': 'test3@example.com',
        'password': 'testpassword123'
    }

