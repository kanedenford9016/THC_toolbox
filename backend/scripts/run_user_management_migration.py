#!/usr/bin/env python3
"""Apply user management migration."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from config.database import db
from config.settings import config

def run_migration():
    """Run the user management migration."""
    try:
        print("[MIGRATION] Running user management migration...")
        
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Add password_changed flag
                print("[MIGRATION] Adding password_changed column...")
                cursor.execute("""
                    ALTER TABLE admin_users
                    ADD COLUMN IF NOT EXISTS password_changed BOOLEAN DEFAULT FALSE
                """)
                
                # Add email column
                print("[MIGRATION] Adding email column...")
                cursor.execute("""
                    ALTER TABLE admin_users
                    ADD COLUMN IF NOT EXISTS email VARCHAR(255)
                """)
                
                # Add temp_password_hash column
                print("[MIGRATION] Adding temp_password_hash column...")
                cursor.execute("""
                    ALTER TABLE admin_users
                    ADD COLUMN IF NOT EXISTS temp_password_hash TEXT
                """)
                
                # Create indexes
                print("[MIGRATION] Creating indexes...")
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email)
                """)
                
                conn.commit()
                
        print("[MIGRATION] ✓ User management migration completed successfully")
        return True
        
    except Exception as e:
        print(f"[MIGRATION] ✗ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
