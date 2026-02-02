"""Member routes."""
from flask import Blueprint, request, jsonify
from app.services.auth import token_required
from app.services.war_session import war_session_service
from app.models.models import Member, FactionConfig, AuditLog

member_bp = Blueprint('members', __name__, url_prefix='/members')

@member_bp.route('/refresh', methods=['POST'])
@token_required
def refresh_members():
    """Refresh members from Torn API."""
    try:
        data = request.get_json()
        
        if not data or 'war_session_id' not in data:
            return jsonify({'error': 'war_session_id is required'}), 400
        
        war_session_id = data['war_session_id']
        faction_id = request.current_user['faction_id']  # type: ignore
        torn_id = request.current_user['torn_id']  # type: ignore
        
        result = war_session_service.sync_members_from_torn(faction_id, war_session_id, torn_id)
        
        # Get last refresh timestamp
        last_refresh = FactionConfig.get_last_refresh(faction_id)
        if last_refresh:
            result['last_refresh_timestamp'] = last_refresh.isoformat()
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@member_bp.route('/<int:member_id>/bonus', methods=['POST'])
@token_required
def add_bonus(member_id):
    """Add or update bonus for a member."""
    try:
        data = request.get_json()
        
        if not data or 'bonus_amount' not in data:
            return jsonify({'error': 'bonus_amount is required'}), 400
        
        bonus_amount = float(data['bonus_amount'])
        bonus_reason = data.get('bonus_reason', '')
        
        if bonus_amount < 0:
            return jsonify({'error': 'Bonus amount must be positive'}), 400
        
        # Get old value for audit
        old_member = Member.get_by_session(None)  # We'll need to adjust this
        
        result = Member.update_bonus(member_id, bonus_amount, bonus_reason)
        
        if not result:
            return jsonify({'error': 'Member not found'}), 404
        
        # Log change
        torn_id = request.current_user['torn_id']  # type: ignore
        AuditLog.create(
            action_type='BONUS_UPDATED',
            user_torn_id=torn_id,
            old_value=None,
            new_value=f"${bonus_amount:,.2f}: {bonus_reason}",
            details=f"Updated bonus for member {member_id}"
        )
        
        return jsonify({'message': 'Bonus updated successfully', 'member_id': member_id}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@member_bp.route('/<int:member_id>/bonus', methods=['PUT'])
@token_required
def update_bonus(member_id):
    """Update bonus for a member (same as POST)."""
    return add_bonus(member_id)

@member_bp.route('/<int:member_id>/bonus', methods=['DELETE'])
@token_required
def delete_bonus(member_id):
    """Delete bonus for a member."""
    try:
        result = Member.delete_bonus(member_id)
        
        if not result:
            return jsonify({'error': 'Member not found'}), 404
        
        # Log deletion
        torn_id = request.current_user['torn_id']  # type: ignore
        AuditLog.create(
            action_type='BONUS_DELETED',
            user_torn_id=torn_id,
            details=f"Deleted bonus for member {member_id}"
        )
        
        return jsonify({'message': 'Bonus deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@member_bp.route('/session/<session_id>', methods=['GET'])
@token_required
def get_session_members(session_id):
    """Get all members for a war session."""
    try:
        members = Member.get_by_session(session_id)
        
        return jsonify({'members': members}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
