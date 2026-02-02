"""Export and archive routes."""
from flask import Blueprint, request, jsonify, send_file
from services.auth import token_required
from services.pdf_report import pdf_report_service
from models.models import AuditLog

export_bp = Blueprint('export', __name__, url_prefix='/export')

@export_bp.route('/<session_id>/pdf', methods=['GET'])
@token_required
def export_pdf(session_id):
    """Export war session as PDF."""
    try:
        # Get user name for footer
        user_name = request.args.get('user_name', 'Administrator')
        
        # Generate PDF
        pdf_buffer = pdf_report_service.generate_war_report(session_id, user_name)
        
        # Log export
        torn_id = request.current_user['torn_id']  # type: ignore
        AuditLog.create(
            action_type='PDF_EXPORTED',
            user_torn_id=torn_id,
            war_session_id=session_id,
            details=f"Exported PDF war report"
        )
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'war_report_{session_id}.pdf'
        )
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


archive_bp = Blueprint('archive', __name__, url_prefix='/archive')

@archive_bp.route('/', methods=['GET'])
@token_required
def get_archived_logs():
    """Query archived audit logs."""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        action_type = request.args.get('action_type')
        limit = int(request.args.get('limit', 100))
        
        # Query archived logs
        logs = AuditLog.get_archived(start_date, end_date, action_type, limit)
        
        return jsonify({'logs': logs, 'count': len(logs)}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@archive_bp.route('/run-archival', methods=['POST'])
@token_required
def run_archival():
    """Manually run the archival process (admin only)."""
    try:
        # This would typically be run via a cron job
        count = AuditLog.archive_old_logs()
        
        # Log the archival
        torn_id = request.current_user['torn_id']  # type: ignore
        AuditLog.create(
            action_type='LOGS_ARCHIVED',
            user_torn_id=torn_id,
            details=f"Archived {count} audit log entries"
        )
        
        return jsonify({
            'message': 'Archival completed successfully',
            'archived_count': count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
