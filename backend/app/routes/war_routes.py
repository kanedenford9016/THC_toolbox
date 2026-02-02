"""War session routes."""
from flask import Blueprint, request, jsonify
from app.services.auth import token_required
from app.services.war_session import war_session_service
from app.services.calculator import calculator_service
from app.models.models import WarSession, Member, OtherPayment, MemberPayout, AuditLog

war_bp = Blueprint('war', __name__, url_prefix='/war')

@war_bp.route('/create', methods=['POST'])
@token_required
def create_war_session():
    """Create a new war session."""
    try:
        data = request.get_json()
        war_name = data.get('war_name', '')
        torn_id = request.current_user['torn_id']  # type: ignore
        faction_id = request.current_user['faction_id']  # type: ignore
        
        result = war_session_service.create_war_session(war_name, torn_id, faction_id)
        
        return jsonify(result), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@war_bp.route('/<session_id>', methods=['GET'])
@token_required
def get_war_details(session_id):
    """Get detailed information for a specific war session."""
    try:
        result = war_session_service.get_war_details(session_id)
        
        if not result:
            return jsonify({'error': 'War session not found'}), 404
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@war_bp.route('/active', methods=['GET'])
@token_required
def get_active_session():
    """Get the active war session."""
    try:
        session = war_session_service.get_active_session()
        
        if not session:
            return jsonify({'message': 'No active war session'}), 404
        
        return jsonify(session), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@war_bp.route('/<session_id>/complete', methods=['POST'])
@token_required
def complete_session(session_id):
    """Complete a war session."""
    try:
        torn_id = request.current_user['torn_id']  # type: ignore
        result = war_session_service.complete_war_session(session_id, torn_id)
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@war_bp.route('/<session_id>/calculate', methods=['POST'])
@token_required
def calculate_payouts(session_id):
    """Calculate payouts for a war session."""
    try:
        data = request.get_json()
        
        if not data or 'total_earnings' not in data or 'price_per_hit' not in data:
            return jsonify({'error': 'total_earnings and price_per_hit are required'}), 400
        
        total_earnings = float(data['total_earnings'])
        price_per_hit = float(data['price_per_hit'])
        
        if total_earnings < 0 or price_per_hit < 0:
            return jsonify({'error': 'Values must be positive'}), 400
        
        print(f"[WAR] Calculating payouts for war {session_id}: earnings=${total_earnings}, price/hit=${price_per_hit}")
        result = calculator_service.calculate_payouts(session_id, total_earnings, price_per_hit)
        
        # Log calculation
        torn_id = request.current_user['torn_id']  # type: ignore
        AuditLog.create(
            action_type='PAYOUT_CALCULATED',
            user_torn_id=torn_id,
            war_session_id=session_id,
            details=f"Calculated payouts: Total ${total_earnings:,.2f}, Price per hit ${price_per_hit:,.2f}"
        )
        
        print(f"[WAR] ✓ Payouts calculated and saved for war {session_id}: {len(result.get('member_payouts', []))} members")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"[WAR] ✗ Error calculating payouts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@war_bp.route('/<session_id>/payouts', methods=['GET'])
@token_required
def get_payouts(session_id):
    """Get payout summary for a war session."""
    try:
        result = calculator_service.get_payout_summary(session_id)
        
        if not result:
            return jsonify({'error': 'War session not found'}), 404
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@war_bp.route('/<session_id>/member-payouts', methods=['GET'])
@token_required
def get_member_payouts(session_id):
    """Get all member payouts for a completed war session."""
    try:
        payouts = MemberPayout.get_by_session(session_id)
        print(f"[WAR] Retrieved {len(payouts)} member payouts for war {session_id}")
        
        return jsonify({'member_payouts': payouts}), 200
        
    except Exception as e:
        print(f"[WAR] ✗ Error getting member payouts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@war_bp.route('/history', methods=['GET'])
@token_required
def get_history():
    """Get all completed war sessions."""
    try:
        sessions = war_session_service.get_completed_sessions()
        
        return jsonify({'sessions': sessions}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@war_bp.route('/list', methods=['GET'])
@token_required
def list_wars():
    """Get all war sessions for the faction."""
    try:
        faction_id = request.current_user['faction_id']  # type: ignore
        sessions = war_session_service.get_faction_wars(faction_id)
        
        return jsonify({'wars': sessions}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
