"""Other payments routes."""
from flask import Blueprint, request, jsonify
from app.services.auth import token_required
from app.models.models import OtherPayment, AuditLog
from typing import Dict, Any, cast

payment_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payment_bp.route('/<session_id>', methods=['POST'])
@token_required
def create_payment(session_id):
    """Create a new other payment."""
    try:
        data = request.get_json()
        
        if not data or 'amount' not in data or 'description' not in data:
            return jsonify({'error': 'amount and description are required'}), 400
        
        amount = float(data['amount'])
        description = data['description']
        
        if amount < 0:
            return jsonify({'error': 'Amount must be positive'}), 400
        
        if not description.strip():
            return jsonify({'error': 'Description cannot be empty'}), 400
        
        torn_id = request.current_user['torn_id']  # type: ignore
        
        result = cast(Dict[str, Any], OtherPayment.create(session_id, amount, description, torn_id))
        
        # Log creation
        AuditLog.create(
            action_type='OTHER_PAYMENT_CREATED',
            user_torn_id=torn_id,
            war_session_id=session_id,
            new_value=f"${amount:,.2f}: {description}",
            details=f"Created other payment"
        )
        
        return jsonify({
            'message': 'Payment created successfully',
            'payment_id': result['payment_id']
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/<session_id>', methods=['GET'])
@token_required
def get_payments(session_id):
    """Get all other payments for a war session."""
    try:
        payments = OtherPayment.get_by_session(session_id)
        
        # Convert amounts to float for proper JSON serialization
        for payment in payments:
            if 'amount' in payment and isinstance(payment['amount'], str):
                try:
                    payment['amount'] = float(payment['amount'])
                except (ValueError, TypeError):
                    payment['amount'] = 0.0
        
        return jsonify({'payments': payments}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/<int:payment_id>', methods=['PUT'])
@token_required
def update_payment(payment_id):
    """Update an other payment."""
    try:
        data = request.get_json()
        
        if not data or 'amount' not in data or 'description' not in data:
            return jsonify({'error': 'amount and description are required'}), 400
        
        amount = float(data['amount'])
        description = data['description']
        
        if amount < 0:
            return jsonify({'error': 'Amount must be positive'}), 400
        
        if not description.strip():
            return jsonify({'error': 'Description cannot be empty'}), 400
        
        result = OtherPayment.update(payment_id, amount, description)
        
        if not result:
            return jsonify({'error': 'Payment not found'}), 404
        
        # Log update
        torn_id = request.current_user['torn_id']  # type: ignore
        AuditLog.create(
            action_type='OTHER_PAYMENT_UPDATED',
            user_torn_id=torn_id,
            new_value=f"${amount:,.2f}: {description}",
            details=f"Updated other payment {payment_id}"
        )
        
        return jsonify({'message': 'Payment updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/<int:payment_id>', methods=['DELETE'])
@token_required
def delete_payment(payment_id):
    """Delete an other payment."""
    try:
        result = OtherPayment.delete(payment_id)
        
        if not result:
            return jsonify({'error': 'Payment not found'}), 404
        
        # Log deletion
        torn_id = request.current_user['torn_id']  # type: ignore
        AuditLog.create(
            action_type='OTHER_PAYMENT_DELETED',
            user_torn_id=torn_id,
            details=f"Deleted other payment {payment_id}"
        )
        
        return jsonify({'message': 'Payment deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
