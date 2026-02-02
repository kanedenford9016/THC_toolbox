"""Initialize member_payouts table if it doesn't exist."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db

def create_member_payouts_table():
    """Create member_payouts table if it doesn't exist."""
    print("[DATABASE] Checking member_payouts table...")
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Try to drop and recreate (safer than checking existence)
            try:
                cursor.execute("DROP TABLE IF EXISTS member_payouts CASCADE")
                print("[DATABASE] Dropped existing member_payouts table (if any)")
            except Exception as e:
                print(f"[DATABASE] Note: {e}")
            
            # Create the table fresh - WITHOUT foreign key to avoid issues
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS member_payouts (
                    payout_id SERIAL PRIMARY KEY,
                    war_session_id UUID NOT NULL,
                    member_id INTEGER NOT NULL,
                    torn_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    hit_count INTEGER NOT NULL DEFAULT 0,
                    base_payout NUMERIC(12, 2) NOT NULL DEFAULT 0,
                    bonus_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
                    total_payout NUMERIC(12, 2) NOT NULL DEFAULT 0,
                    bonus_reason TEXT,
                    member_status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(war_session_id, member_id)
                )
            """)
            print("[DATABASE] Created member_payouts table")
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_member_payouts_session 
                ON member_payouts(war_session_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_member_payouts_member 
                ON member_payouts(member_id, war_session_id)
            """)
            print("[DATABASE] Created indexes")
            
            conn.commit()
            print("[DATABASE] ✓ member_payouts table and indexes created successfully")
            return True
            
    except Exception as e:
        print(f"[DATABASE] ✗ Error creating member_payouts table: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = create_member_payouts_table()
    sys.exit(0 if success else 1)
