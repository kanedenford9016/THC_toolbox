"""Authentication service with JWT tokens."""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, Request
from config.settings import config
from services.torn_api import torn_api_service
from models.models import FactionConfig, AuditLog, AdminUser
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Any

# Extend Flask Request to include current_user attribute
setattr(Request, 'current_user', None)

# In-memory session tracking for activity
active_sessions = {}

class AuthService:
    """Service for authentication and authorization."""
    
    @staticmethod
    def login(username, password, torn_api_key):
        """
        Authenticate user with Torn username, password, and API key.
        
        Args:
            username: Torn username (must match Torn API user name)
            password: User-chosen password
            torn_api_key: Torn API key (cached only for the session)
            
        Returns:
            dict: Authentication result with tokens and user info
        """
        # Validate API key and get user info
        user_data = torn_api_service.validate_api_key(torn_api_key)
        
        if not user_data:
            return None, "Invalid API key or unable to fetch user data"
        
        torn_id = user_data.get('player_id')
        torn_name = user_data.get('name')
        faction_id = user_data.get('faction_id')

        if not torn_name or torn_name.lower() != username.lower():
            return None, "Username must match your Torn username"
        
        if not torn_id or not faction_id:
            return None, "Invalid user data from Torn API"
        
        # For initial setup, skip faction admin verification
        # (can be re-enabled later for production)
        faction_info = {
            'faction_id': faction_id,
            'faction_name': f'Faction {faction_id}',
            'position': 'member'
        }

        # Create or verify admin user
        existing_admin = AdminUser.get_by_username(username)
        password_needs_change = False
        
        if existing_admin:
            if not check_password_hash(existing_admin['password_hash'], password):
                return None, "Invalid username or password"
            password_needs_change = not existing_admin.get('password_changed', True)
        else:
            password_hash = generate_password_hash(password)
            AdminUser.create(
                torn_id=torn_id,
                username=username,
                password_hash=password_hash,
                faction_id=faction_info['faction_id'],
                email=None,  # type: ignore
                password_changed=True  # Initial login doesn't require change
            )
        
        # Store faction config (no API key stored)
        FactionConfig.create(
            faction_id=faction_info['faction_id'],
            faction_name=faction_info['faction_name']
        )
        
        # Generate tokens
        access_token = AuthService.generate_access_token(torn_id, faction_info['faction_id'])
        refresh_token = AuthService.generate_refresh_token(torn_id, faction_info['faction_id'])
        
        # Initialize session tracking (cache API key for session only)
        active_sessions[torn_id] = {
            'last_activity': datetime.utcnow(),
            'faction_id': faction_info['faction_id'],
            'api_key': torn_api_key
        }
        
        # Log authentication
        AuditLog.create(
            action_type='USER_LOGIN',
            user_torn_id=torn_id,
            details=f"User logged in as {faction_info['position']}"
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'torn_id': torn_id,
                'name': torn_name,
                'faction_id': faction_info['faction_id'],
                'faction_name': faction_info['faction_name'],
                'position': faction_info['position']
            },
            'password_needs_change': password_needs_change
        }, None
    
    @staticmethod
    def generate_access_token(torn_id, faction_id):
        """Generate JWT access token."""
        if not config.JWT_SECRET:
            raise ValueError("JWT_SECRET not configured")
        
        payload = {
            'torn_id': torn_id,
            'faction_id': faction_id,
            'type': 'access',
            'exp': datetime.utcnow() + timedelta(hours=config.ACCESS_TOKEN_EXPIRY_HOURS),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, config.JWT_SECRET, algorithm='HS256')
    
    @staticmethod
    def generate_refresh_token(torn_id, faction_id):
        """Generate JWT refresh token."""
        if not config.JWT_SECRET:
            raise ValueError("JWT_SECRET not configured")
        
        payload = {
            'torn_id': torn_id,
            'faction_id': faction_id,
            'type': 'refresh',
            'exp': datetime.utcnow() + timedelta(days=config.REFRESH_TOKEN_EXPIRY_DAYS),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, config.JWT_SECRET, algorithm='HS256')
    
    @staticmethod
    def verify_token(token):
        """Verify and decode JWT token."""
        try:
            if not config.JWT_SECRET:
                return None, "JWT_SECRET not configured"
            
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
            return payload, None
        except jwt.ExpiredSignatureError:
            return None, "Token has expired"
        except jwt.InvalidTokenError:
            return None, "Invalid token"
    
    @staticmethod
    def check_session_activity(torn_id):
        """Check if user session is still active based on inactivity timeout."""
        if torn_id not in active_sessions:
            return False
        
        session = active_sessions[torn_id]
        last_activity = session['last_activity']
        timeout = timedelta(minutes=config.SESSION_TIMEOUT_MINUTES)
        
        if datetime.utcnow() - last_activity > timeout:
            # Session expired due to inactivity
            del active_sessions[torn_id]
            return False
        
        return True
    
    @staticmethod
    def update_activity(torn_id):
        """Update last activity timestamp for user."""
        if torn_id in active_sessions:
            active_sessions[torn_id]['last_activity'] = datetime.utcnow()

    @staticmethod
    def get_session_api_key(torn_id):
        """Get cached Torn API key for current session (not stored in DB)."""
        session = active_sessions.get(torn_id)
        if not session:
            return None
        return session.get('api_key')
    
    @staticmethod
    def logout(torn_id):
        """Logout user and clear session."""
        if torn_id in active_sessions:
            del active_sessions[torn_id]
        
        AuditLog.create(
            action_type='USER_LOGOUT',
            user_torn_id=torn_id,
            details="User logged out"
        )
    
    @staticmethod
    def refresh_access_token(refresh_token):
        """Generate new access token from refresh token."""
        payload, error = AuthService.verify_token(refresh_token)
        
        if error:
            return None, error
        
        if not payload or payload.get('type') != 'refresh':
            return None, "Invalid token type"
        
        torn_id = payload.get('torn_id')
        faction_id = payload.get('faction_id')
        
        # Generate new access token
        new_access_token = AuthService.generate_access_token(torn_id, faction_id)
        
        # Update session activity
        if torn_id in active_sessions:
            active_sessions[torn_id]['last_activity'] = datetime.utcnow()
        
        return new_access_token, None


def token_required(f):
    """Decorator to require valid JWT access token for routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        # Get token from cookie as fallback
        if not token:
            token = request.cookies.get('access_token')
        
        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401
        
        # Verify token
        payload, error = AuthService.verify_token(token)
        
        if error:
            return jsonify({'error': error}), 401
        
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Verify token type is 'access' (not 'refresh')
        if payload.get('type') != 'access':
            return jsonify({'error': 'Invalid token type. Expected access token'}), 401
        
        # Check session activity
        torn_id = payload.get('torn_id')
        if not AuthService.check_session_activity(torn_id):
            return jsonify({'error': 'Session expired due to inactivity. Please login again'}), 401
        
        # Update last activity
        AuthService.update_activity(torn_id)
        
        # Add user info to request context
        if payload:
            request.current_user = payload  # type: ignore
        
        return f(*args, **kwargs)
    
    return decorated

# Additional auth functions
import secrets
import string

auth_service = AuthService()

def generate_temporary_password(length=12):
    """Generate a temporary password."""
    characters = string.ascii_letters + string.digits + string.punctuation.replace("'\"\\", "")
    return ''.join(secrets.choice(characters) for _ in range(length))

