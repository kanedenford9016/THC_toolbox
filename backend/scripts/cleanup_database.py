#!/usr/bin/env python3
"""Clean up database - keep only RedDragon2010, delete all wars."""

import sys
import os

# Add the backend directory to the path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from config.database import db

def cleanup_database():
    """Clean up database."""
    try:
        print("[CLEANUP] Starting database cleanup...")
        
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Delete all wars and related data
                print("[CLEANUP] Deleting all war sessions and related data...")
                cursor.execute("DELETE FROM members WHERE war_session_id IN (SELECT session_id FROM war_sessions)")
                cursor.execute("DELETE FROM other_payments WHERE war_session_id IN (SELECT session_id FROM war_sessions)")
                cursor.execute("DELETE FROM member_payouts WHERE war_session_id IN (SELECT session_id FROM war_sessions)")
                cursor.execute("DELETE FROM war_sessions")
                
                # Delete all admin users except RedDragon2010
                print("[CLEANUP] Deleting all admin users except RedDragon2010...")
                cursor.execute("DELETE FROM admin_users WHERE username != %s", ('RedDragon2010',))
                
                conn.commit()
                
        print("[CLEANUP] ✓ Database cleanup completed successfully")
        print("[CLEANUP] - Deleted all war sessions and related data")
        print("[CLEANUP] - Kept only RedDragon2010 login profile")
        return True
        
    except Exception as e:
        print(f"[CLEANUP] ✗ Cleanup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = cleanup_database()
    sys.exit(0 if success else 1)
