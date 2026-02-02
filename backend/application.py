"""Main Flask application."""
import os
import sys
from pathlib import Path

# Ensure backend directory is in path for imports
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config.settings import config

# CORS origins are loaded from environment variables

# Ensure backend/modules package directory is importable
modules_dir = backend_dir / "modules"
sys.path.insert(0, str(modules_dir))

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    
    # SKIP database initialization for now - can cause issues in serverless
    # These will be run separately or on-demand
    
    # Configure CORS - use resources to apply to all routes
    # Manual CORS headers
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin and any(origin == allowed for allowed in config.CORS_ORIGINS):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    # Handle OPTIONS requests for CORS preflight
    @app.before_request
    def handle_preflight():
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            origin = request.headers.get('Origin')
            if origin and any(origin == allowed for allowed in config.CORS_ORIGINS):
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Credentials'] = 'true'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
    
    # Configure rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["1000 per day", "200 per hour"],
        storage_uri="memory://"
    )
    
    # Apply rate limit to Torn API routes
    @app.before_request
    def check_torn_api_rate_limit():
        # This will be handled in the torn_api service
        pass
    
    # Register blueprints
    from modules.routes.auth_routes import auth_bp
    from modules.routes.war_routes import war_bp
    from modules.routes.member_routes import member_bp
    from modules.routes.payment_routes import payment_bp
    from modules.routes.export_routes import export_bp, archive_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(war_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(archive_bp)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'torn-war-calculator'}), 200
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'service': 'Torn Faction War Calculator API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/auth/*',
                'war': '/war/*',
                'members': '/members/*',
                'payments': '/payments/*',
                'export': '/export/*',
                'archive': '/archive/*'
            }
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
    
    return app

# Expose app factory for serverless runtimes (e.g., Vercel)
# App will be created in api.py and wsgi.py entry points

if __name__ == '__main__':
    app = create_app()
    
    # Validate configuration
    try:
        config.validate()
        print("[OK] Configuration validated successfully")
    except ValueError as e:
        print(f"[ERROR] Configuration error: {e}")
        exit(1)
    
    # Run the app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=config.DEBUG)
