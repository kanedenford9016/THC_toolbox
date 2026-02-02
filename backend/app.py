"""Main Flask application."""
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config.settings import config
import os

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    
    # Initialize database tables
    print("[APP] Initializing database tables...")
    try:
        from scripts.init_member_payouts_table import create_member_payouts_table
        create_member_payouts_table()
        print("[APP] ✓ Database tables initialized")
    except Exception as e:
        print(f"[APP] ✗ Could not initialize member_payouts table: {e}")
        import traceback
        traceback.print_exc()
    
    # Run user management migration
    print("[APP] Running user management migration...")
    try:
        from scripts.run_user_management_migration import run_migration
        if run_migration():
            print("[APP] ✓ User management migration completed")
    except Exception as e:
        print(f"[APP] ⚠ Could not run user management migration: {e}")
        import traceback
        traceback.print_exc()
    
    # Configure CORS
    CORS(app, 
         origins=config.CORS_ORIGINS,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'])
    
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
    from app.routes.auth_routes import auth_bp
    from app.routes.war_routes import war_bp
    from app.routes.member_routes import member_bp
    from app.routes.payment_routes import payment_bp
    from app.routes.export_routes import export_bp, archive_bp
    
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
