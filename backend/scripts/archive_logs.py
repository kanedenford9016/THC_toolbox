"""Cron job script for archiving old audit logs."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.models import AuditLog
from datetime import datetime

def run_archival():
    """Run the audit log archival process."""
    try:
        print(f"[{datetime.now().isoformat()}] Starting audit log archival...")
        
        count = AuditLog.archive_old_logs()
        
        print(f"[{datetime.now().isoformat()}] Successfully archived {count} audit log entries")
        
        # Log the archival itself
        AuditLog.create(
            action_type='AUTOMATED_ARCHIVAL',
            user_torn_id=0,  # System user
            details=f"Automated archival: {count} entries archived"
        )
        
        return count
        
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error during archival: {str(e)}")
        raise e

if __name__ == '__main__':
    try:
        archived_count = run_archival()
        print(f"Archival completed: {archived_count} records archived")
        sys.exit(0)
    except Exception as e:
        print(f"Archival failed: {str(e)}")
        sys.exit(1)
