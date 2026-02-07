"""Flask application initialization and configuration."""
import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv

from backend.config.database import db_connection
from backend.routes.auth import auth_bp
from backend.routes.matching import matching_bp
from backend.routes.pods import pods_bp
from backend.routes.messages import messages_bp, init_socketio, register_socketio_handlers

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # CORS configuration
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
    CORS(app, origins=cors_origins, supports_credentials=True)
    
    # Register blueprints first (before rate limiter setup)
    app.register_blueprint(auth_bp)
    app.register_blueprint(matching_bp)
    app.register_blueprint(pods_bp)
    app.register_blueprint(messages_bp)
    
    # Initialize rate limiter
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    from backend.routes.matching import init_limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    app.config['RATELIMIT_ENABLED'] = True
    init_limiter(limiter)
    
    # Initialize SocketIO
    socketio = SocketIO(
        app,
        cors_allowed_origins=cors_origins,
        async_mode='threading',
        logger=True,
        engineio_logger=True
    )
    
    # Initialize SocketIO in messages module
    init_socketio(socketio)
    register_socketio_handlers(socketio)
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad request',
            'code': 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'code': 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'code': 403
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not found',
            'code': 404
        }), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate limit exceeded',
            'code': 429
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f'Internal server error: {str(error)}', exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'code': 500
        }), 500
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        try:
            # Check database connection
            db_healthy = db_connection.health_check()
            
            return jsonify({
                'status': 'healthy' if db_healthy else 'unhealthy',
                'database': 'connected' if db_healthy else 'disconnected'
            }), 200 if db_healthy else 503
        except Exception as e:
            logger.error(f'Health check failed: {str(e)}')
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 503
    
    # Request logging middleware
    @app.before_request
    def log_request():
        """Log incoming requests."""
        logger.info(f'{request.method} {request.path} - {request.remote_addr}')
    
    @app.after_request
    def log_response(response):
        """Log outgoing responses."""
        logger.info(f'{request.method} {request.path} - Status: {response.status_code}')
        return response
    
    return app


# Create app instance
app = create_app()

# Get SocketIO instance - it's initialized in create_app and stored in messages module
from backend.routes.messages import socketio

# Store socketio in app for access
app.socketio = socketio

if __name__ == '__main__':
    # Run the application
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f'Starting Flask application on port {port}')
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)

