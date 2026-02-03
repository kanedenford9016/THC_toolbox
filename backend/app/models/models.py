"""Database models for the application."""
from config.database import db
from utils.encryption import encryption_service
from datetime import datetime, timedelta, date
from config.settings import config
from typing import Dict, List, Any, Optional, cast

class FactionConfig:
    """Model for faction configuration."""
    
    @staticmethod
    def create(faction_id, faction_name):
        """Create or update faction configuration (no API key stored)."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO faction_config (faction_id, faction_name, encrypted_torn_api_key)
                VALUES (%s, %s, NULL)
                ON CONFLICT (faction_id) 
                DO UPDATE SET 
                    faction_name = EXCLUDED.faction_name,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, faction_id, faction_name, last_api_refresh_timestamp
            """, (faction_id, faction_name))
            return cursor.fetchone()
    
    @staticmethod
    def get_api_key(faction_id):
        """API keys are not stored. Always returns None."""
        return None
    
    @staticmethod
    def update_refresh_timestamp(faction_id):
        """Update last API refresh timestamp."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE faction_config 
                SET last_api_refresh_timestamp = CURRENT_TIMESTAMP
                WHERE faction_id = %s
                RETURNING last_api_refresh_timestamp
            """, (faction_id,))
            return cursor.fetchone()
    
    @staticmethod
    def get_last_refresh(faction_id):
        """Get last API refresh timestamp."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT last_api_refresh_timestamp FROM faction_config WHERE faction_id = %s
            """, (faction_id,))
            result: Optional[Dict[str, Any]] = cast(Optional[Dict[str, Any]], cursor.fetchone())
            return result.get('last_api_refresh_timestamp') if result else None


class AdminUser:
    """Model for admin users (Torn username + password hash)."""

    @staticmethod
    def get_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Get admin user by username."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM admin_users WHERE username = %s
            """, (username,))
            return cast(Optional[Dict[str, Any]], cursor.fetchone())

    @staticmethod
    def get_all() -> list:
        """Get all admin users (without sensitive data)."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT admin_id, torn_id, username, email, faction_id, password_changed, created_at, updated_at
                FROM admin_users
                ORDER BY username
            """)
            return cursor.fetchall()

    @staticmethod
    def create(torn_id: int, username: str, password_hash: str, faction_id: int, email: str = None, password_changed: bool = False):  # type: ignore
        """Create a new admin user."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO admin_users (torn_id, username, password_hash, faction_id, email, password_changed)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING admin_id, torn_id, username, faction_id, email, password_changed
            """, (torn_id, username, password_hash, faction_id, email, password_changed))
            return cursor.fetchone()

    @staticmethod
    def update_password(username: str, new_password_hash: str, mark_changed: bool = True):
        """Update user password and mark as changed."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE admin_users
                SET password_hash = %s, password_changed = %s
                WHERE username = %s
                RETURNING admin_id, username
            """, (new_password_hash, mark_changed, username))
            return cursor.fetchone()


class WarSession:
    """Model for war sessions."""
    
    @staticmethod
    def create(war_name, created_by_torn_id, ranked_war_id=None, opposing_faction_name=None, war_start_timestamp=None, war_end_timestamp=None):
        """Create a new war session."""
        with db.get_cursor() as cursor:
            # Check for existing active session
            cursor.execute("SELECT session_id FROM war_sessions WHERE status = 'active'")
            active = cursor.fetchone()
            
            if active:
                raise ValueError("An active war session already exists. Complete it before creating a new one.")
            
            cursor.execute("""
                INSERT INTO war_sessions (
                    war_name, status, created_by_torn_id,
                    ranked_war_id, opposing_faction_name, war_start_timestamp, war_end_timestamp
                )
                VALUES (%s, 'active', %s, %s, %s, %s, %s)
                RETURNING session_id, war_name, status, created_timestamp,
                          ranked_war_id, opposing_faction_name, war_start_timestamp, war_end_timestamp
            """, (war_name, created_by_torn_id, ranked_war_id, opposing_faction_name, war_start_timestamp, war_end_timestamp))
            return cursor.fetchone()
    
    @staticmethod
    def get_active():
        """Get the active war session."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM war_sessions WHERE status = 'active'
            """)
            result: Optional[Dict[str, Any]] = cast(Optional[Dict[str, Any]], cursor.fetchone())
            
            if result:
                # Decrypt sensitive fields
                if result.get('encrypted_total_paid'):
                    result['total_paid'] = encryption_service.decrypt(result['encrypted_total_paid'])
                if result.get('encrypted_remaining_balance'):
                    result['remaining_balance'] = encryption_service.decrypt(result['encrypted_remaining_balance'])
            
            return result
    
    @staticmethod
    def update_calculations(session_id, total_earnings, price_per_hit, total_paid, remaining_balance):
        """Update war session calculations."""
        encrypted_total_paid = encryption_service.encrypt(str(total_paid))
        encrypted_remaining = encryption_service.encrypt(str(remaining_balance))
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE war_sessions 
                SET total_earnings = %s,
                    price_per_hit = %s,
                    encrypted_total_paid = %s,
                    encrypted_remaining_balance = %s
                WHERE session_id = %s
                RETURNING session_id
            """, (total_earnings, price_per_hit, encrypted_total_paid, encrypted_remaining, session_id))
            return cursor.fetchone()
    
    @staticmethod
    def complete(session_id):
        """Mark war session as completed."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE war_sessions 
                SET status = 'completed',
                    completed_timestamp = CURRENT_TIMESTAMP
                WHERE session_id = %s
                RETURNING session_id, status, completed_timestamp
            """, (session_id,))
            return cursor.fetchone()
    
    @staticmethod
    def get_all_completed():
        """Get all completed war sessions."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT session_id, war_name, created_timestamp, completed_timestamp,
                       total_earnings, price_per_hit
                FROM war_sessions 
                WHERE status = 'completed'
                ORDER BY completed_timestamp DESC
            """)
            return cursor.fetchall()

    @staticmethod
    def get_by_faction(faction_id: int):
        """Get all war sessions for a faction."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT ws.session_id, ws.war_name, ws.created_timestamp, ws.completed_timestamp,
                       ws.status, ws.total_earnings, ws.price_per_hit,
                       ws.ranked_war_id, ws.opposing_faction_name,
                       ws.war_start_timestamp, ws.war_end_timestamp,
                       COUNT(DISTINCT m.member_id) as member_count
                FROM war_sessions ws
                LEFT JOIN admin_users au ON ws.created_by_torn_id = au.torn_id
                LEFT JOIN members m ON ws.session_id = m.war_session_id
                WHERE au.faction_id = %s
                GROUP BY ws.session_id
                ORDER BY ws.created_timestamp DESC
            """, (faction_id,))
            return cursor.fetchall()

    @staticmethod
    def get_by_id(session_id):
        """Get a war session by ID."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM war_sessions WHERE session_id = %s
            """, (session_id,))
            return cursor.fetchone()


class Member:
    """Model for faction members."""
    
    @staticmethod
    def upsert(war_session_id, torn_id, name, hit_count, score=None, member_status='active'):
        """Create or update member in war session."""
        encrypted_hits = encryption_service.encrypt(str(hit_count))
        encrypted_score = encryption_service.encrypt(str(score)) if score is not None else None
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO members (war_session_id, torn_id, name, encrypted_hit_count, encrypted_score, member_status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (torn_id, war_session_id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    encrypted_hit_count = EXCLUDED.encrypted_hit_count,
                    encrypted_score = EXCLUDED.encrypted_score,
                    member_status = EXCLUDED.member_status,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING member_id
            """, (war_session_id, torn_id, name, encrypted_hits, encrypted_score, member_status))
            return cursor.fetchone()
    
    @staticmethod
    def get_by_session(war_session_id):
        """Get all members for a war session."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM members WHERE war_session_id = %s
                ORDER BY name
            """, (war_session_id,))
            results: List[Dict[str, Any]] = cast(List[Dict[str, Any]], cursor.fetchall())
            
            # Decrypt sensitive fields
            for result in results:
                if result.get('encrypted_hit_count'):
                    result['hit_count'] = encryption_service.decrypt(result['encrypted_hit_count'])
                if result.get('encrypted_score'):
                    result['score'] = encryption_service.decrypt(result['encrypted_score'])
                if result.get('encrypted_bonus_amount'):
                    result['bonus_amount'] = encryption_service.decrypt(result['encrypted_bonus_amount'])
            
            return results
    
    @staticmethod
    def update_bonus(member_id, bonus_amount, bonus_reason):
        """Update member bonus."""
        encrypted_bonus = encryption_service.encrypt(str(bonus_amount)) if bonus_amount else None
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE members 
                SET encrypted_bonus_amount = %s,
                    bonus_reason = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE member_id = %s
                RETURNING member_id
            """, (encrypted_bonus, bonus_reason, member_id))
            return cursor.fetchone()
    
    @staticmethod
    def delete_bonus(member_id):
        """Remove member bonus."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE members 
                SET encrypted_bonus_amount = NULL,
                    bonus_reason = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE member_id = %s
                RETURNING member_id
            """, (member_id,))
            return cursor.fetchone()
    
    @staticmethod
    def update_status(war_session_id, torn_id, status):
        """Update member status."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE members 
                SET member_status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE war_session_id = %s AND torn_id = %s
                RETURNING member_id
            """, (status, war_session_id, torn_id))
            return cursor.fetchone()


class OtherPayment:
    """Model for other payments."""
    
    @staticmethod
    def create(war_session_id, amount, description, created_by_torn_id):
        """Create a new other payment."""
        encrypted_amount = encryption_service.encrypt(str(amount))
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO other_payments (war_session_id, encrypted_amount, description, created_by_torn_id)
                VALUES (%s, %s, %s, %s)
                RETURNING payment_id, created_at
            """, (war_session_id, encrypted_amount, description, created_by_torn_id))
            return cursor.fetchone()
    
    @staticmethod
    def get_by_session(war_session_id):
        """Get all other payments for a war session."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM other_payments WHERE war_session_id = %s
                ORDER BY created_at
            """, (war_session_id,))
            results: List[Dict[str, Any]] = cast(List[Dict[str, Any]], cursor.fetchall())
            
            # Decrypt amounts
            for result in results:
                if result.get('encrypted_amount'):
                    result['amount'] = encryption_service.decrypt(result['encrypted_amount'])
            
            return results
    
    @staticmethod
    def update(payment_id, amount, description):
        """Update an other payment."""
        encrypted_amount = encryption_service.encrypt(str(amount))
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE other_payments 
                SET encrypted_amount = %s,
                    description = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE payment_id = %s
                RETURNING payment_id
            """, (encrypted_amount, description, payment_id))
            return cursor.fetchone()
    
    @staticmethod
    def delete(payment_id):
        """Delete an other payment."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM other_payments WHERE payment_id = %s
                RETURNING payment_id
            """, (payment_id,))
            return cursor.fetchone()


class MemberPayout:
    """Model for member payouts calculated for a war session."""
    
    @staticmethod
    def create(war_session_id, member_id, torn_id, name, hit_count, base_payout, bonus_amount, total_payout, bonus_reason=None, member_status='active'):
        """Create a member payout record."""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO member_payouts 
                    (war_session_id, member_id, torn_id, name, hit_count, base_payout, bonus_amount, total_payout, bonus_reason, member_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING payout_id
                """, (war_session_id, member_id, torn_id, name, hit_count, base_payout, bonus_amount, total_payout, bonus_reason, member_status))
                result = cursor.fetchone()
                payout_id = result.get('payout_id') if result else 'N/A'  # type: ignore
                print(f"[PAYOUT_MODEL] ✓ Created payout for {name}: payout_id={payout_id}")
                return result
        except Exception as e:
            print(f"[PAYOUT_MODEL] ✗ Error creating payout for {name}: {e}")
            raise
    
    @staticmethod
    def get_by_session(war_session_id):
        """Get all member payouts for a war session with member data."""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        mp.*,
                        COALESCE(m.encrypted_hit_count, '') as encrypted_hit_count,
                        COALESCE(m.encrypted_score, '') as encrypted_score
                    FROM member_payouts mp
                    LEFT JOIN members m 
                        ON mp.war_session_id = m.war_session_id 
                        AND mp.member_id = m.member_id
                    WHERE mp.war_session_id = %s
                    ORDER BY mp.name
                """, (war_session_id,))
                results = cursor.fetchall()
                
                # Decrypt the encrypted fields
                from services.auth import encryption_service
                for result in results:
                    if result.get('encrypted_hit_count'):
                        try:
                            result['attacks'] = int(encryption_service.decrypt(result['encrypted_hit_count']))
                        except:
                            result['attacks'] = 0
                    else:
                        result['attacks'] = 0
                    
                    if result.get('encrypted_score'):
                        try:
                            result['respect'] = float(encryption_service.decrypt(result['encrypted_score']))
                        except:
                            result['respect'] = 0.0
                    else:
                        result['respect'] = 0.0
                    
                    # Effective hits is the same as attacks for this context
                    result['effective_hits'] = result['attacks']
                
                print(f"[PAYOUT_MODEL] ✓ Retrieved {len(results)} payouts for war {war_session_id}")
                return results
        except Exception as e:
            print(f"[PAYOUT_MODEL] ✗ Error getting payouts: {e}")
            raise
    
    @staticmethod
    def delete_by_session(war_session_id):
        """Delete all member payouts for a war session (for recalculation)."""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM member_payouts WHERE war_session_id = %s
                    RETURNING payout_id
                """, (war_session_id,))
                deleted = cursor.rowcount
                print(f"[PAYOUT_MODEL] ✓ Deleted {deleted} existing payouts for war {war_session_id}")
                return deleted
        except Exception as e:
            print(f"[PAYOUT_MODEL] ✗ Error deleting payouts: {e}")
            raise


class AuditLog:
    """Model for audit logs."""
    
    @staticmethod
    def create(action_type, user_torn_id, war_session_id=None, old_value=None, new_value=None, details=None):
        """Create a new audit log entry."""
        encrypted_old = encryption_service.encrypt(str(old_value)) if old_value else None
        encrypted_new = encryption_service.encrypt(str(new_value)) if new_value else None
        encrypted_details = encryption_service.encrypt(str(details)) if details else None
        
        retention_date = date.today() + timedelta(days=config.AUDIT_LOG_RETENTION_DAYS)
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO audit_logs 
                (action_type, user_torn_id, war_session_id, encrypted_old_value, 
                 encrypted_new_value, encrypted_details, retention_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING log_id, timestamp
            """, (action_type, user_torn_id, war_session_id, encrypted_old, encrypted_new, 
                  encrypted_details, retention_date))
            return cursor.fetchone()
    
    @staticmethod
    def get_by_session(war_session_id, limit=100):
        """Get audit logs for a war session."""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM audit_logs 
                WHERE war_session_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (war_session_id, limit))
            return cursor.fetchall()
    
    @staticmethod
    def archive_old_logs():
        """Archive logs past retention date."""
        with db.get_cursor() as cursor:
            # Move to archive
            cursor.execute("""
                INSERT INTO audit_logs_archived 
                SELECT * FROM audit_logs 
                WHERE retention_date < CURRENT_DATE
            """)
            
            archived_count = cursor.rowcount
            
            # Delete from main table
            cursor.execute("""
                DELETE FROM audit_logs 
                WHERE retention_date < CURRENT_DATE
            """)
            
            return archived_count
    
    @staticmethod
    def get_archived(start_date=None, end_date=None, action_type=None, limit=100):
        """Query archived logs."""
        query = "SELECT * FROM audit_logs_archived WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date)
        
        if action_type:
            query += " AND action_type = %s"
            params.append(action_type)
        
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        
        with db.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
