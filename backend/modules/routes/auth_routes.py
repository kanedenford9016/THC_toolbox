"""Authentication routes."""
from flask import Blueprint, request, jsonify, make_response
from modules.services.auth import auth_service, token_required
from datetime import datetime, timedelta
from config.settings import config
from typing import Dict, Any, cast

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with Torn username, password, and API key."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Username, password, and API key are required'}), 400

        username = data.get('username')
        password = data.get('password')
        torn_api_key = data.get('torn_api_key')
        
        if not username or not password or not torn_api_key:
            return jsonify({'error': 'Username, password, and API key are required'}), 400
        
        # Attempt login
        result, error = auth_service.login(username, password, torn_api_key)
        
        if error:
            return jsonify({'error': error}), 401
        
        # Create response with tokens
        result_dict: Dict[str, Any] = cast(Dict[str, Any], result)
        response = make_response(jsonify({
            'message': 'Login successful',
            'user': result_dict['user'],
            'access_token': result_dict['access_token'],
            'refresh_token': result_dict['refresh_token']
        }))
        
        # Set HTTP-only cookies for tokens
        response.set_cookie(
            'access_token',
            result_dict['access_token'],
            httponly=True,
            secure=True,
            samesite='Strict',
            max_age=config.ACCESS_TOKEN_EXPIRY_HOURS * 3600
        )
        
        response.set_cookie(
            'refresh_token',
            result_dict['refresh_token'],
            httponly=True,
            secure=True,
            samesite='Strict',
            max_age=config.REFRESH_TOKEN_EXPIRY_DAYS * 86400
        )
        
        return response, 200
        
    except Exception as e:
        print(f"[ERROR] Login failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token using refresh token."""
    try:
        refresh_token = request.cookies.get('refresh_token')

        if not refresh_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                refresh_token = auth_header.split(' ')[1]

        if not refresh_token:
            data = request.get_json(silent=True) or {}
            refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token not found'}), 401
        
        new_access_token, error = auth_service.refresh_access_token(refresh_token)
        
        if error or not new_access_token:
            return jsonify({'error': error or 'Failed to refresh token'}), 401
        
        # Create response with new access token
        response = make_response(jsonify({
            'message': 'Token refreshed successfully',
            'access_token': new_access_token
        }))
        
        response.set_cookie(
            'access_token',
            new_access_token,
            httponly=True,
            secure=True,
            samesite='Strict',
            max_age=config.ACCESS_TOKEN_EXPIRY_HOURS * 3600
        )
        
        return response, 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user (best-effort even if token is missing)."""
    try:
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        if not token:
            token = request.cookies.get('access_token')

        if token:
            payload, _ = auth_service.verify_token(token)
            if payload and payload.get('torn_id'):
                auth_service.logout(payload.get('torn_id'))
        
        # Create response
        response = make_response(jsonify({'message': 'Logout successful'}))
        
        # Clear cookies
        response.set_cookie('access_token', '', expires=0)
        response.set_cookie('refresh_token', '', expires=0)
        
        return response, 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify():
    """Verify token and get current user info."""
    try:
        return jsonify({
            'user': {
                'torn_id': request.current_user['torn_id'],  # type: ignore
                'faction_id': request.current_user['faction_id']  # type: ignore
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@auth_bp.route('/users', methods=['GET'])
@token_required
def list_users():
    """List all admin users (requires authentication)."""
    try:
        from models.models import AdminUser
        users = AdminUser.get_all()
        return jsonify({
            'users': users
        }), 200
    except Exception as e:
        print(f"[ERROR] Failed to list users: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/create-user', methods=['POST'])
@token_required
def create_user():
    """Create a new admin user with temporary password."""
    try:
        from models.models import AdminUser
        from services.auth import generate_temporary_password
        from werkzeug.security import generate_password_hash
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Username, email, torn_id, and faction_id are required'}), 400
        
        username = data.get('username')
        email = data.get('email')
        torn_id = data.get('torn_id')
        faction_id = data.get('faction_id')
        
        if not username or not torn_id or not faction_id:
            return jsonify({'error': 'Username, torn_id, and faction_id are required'}), 400
        
        # Check if username already exists
        existing = AdminUser.get_by_username(username)
        if existing:
            return jsonify({'error': 'Username already exists'}), 409
        
        # Generate temporary password
        temp_password = generate_temporary_password()
        password_hash = generate_password_hash(temp_password)
        
        # Create user (password_changed = False so they must change it)
        user = AdminUser.create(
            torn_id=torn_id,
            username=username,
            password_hash=password_hash,
            faction_id=faction_id,
            email=email,
            password_changed=False
        )
        
        # Log the creation
        from models.models import AuditLog
        AuditLog.create(
            action_type='USER_CREATED',
            user_torn_id=request.current_user['torn_id'],  # type: ignore
            details=f"Created user {username} (torn_id: {torn_id})"
        )
        
        return jsonify({
            'message': 'User created successfully',
            'user': user,
            'temporary_password': temp_password,
            'note': 'User must change this password on first login'
        }), 201
        
    except Exception as e:
        print(f"[ERROR] Failed to create user: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Change password for current user."""
    try:
        from models.models import AdminUser
        from werkzeug.security import generate_password_hash, check_password_hash
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters'}), 400
        
        # Get current user from token
        torn_id = request.current_user['torn_id']  # type: ignore
        
        # Get user by torn_id (need a new model method for this)
        from config.database import db
        with db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM admin_users WHERE torn_id = %s", (torn_id,))
            user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify current password
        if not check_password_hash(user.get('password_hash'), current_password):  # type: ignore
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Hash new password and update
        new_password_hash = generate_password_hash(new_password)
        result = AdminUser.update_password(user.get('username'), new_password_hash, mark_changed=True)  # type: ignore
        
        # Log the password change
        from models.models import AuditLog
        AuditLog.create(
            action_type='PASSWORD_CHANGED',
            user_torn_id=torn_id,
            details=f"User {user.get('username')} changed password"  # type: ignore
        )
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Failed to change password: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500