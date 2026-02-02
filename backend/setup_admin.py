"""
Setup script to create the initial admin user.
This script will:
1. Apply the database migrations if needed
2. Create your first admin account
"""

import sys
import os
from getpass import getpass
import requests

# Add the backend directory to the path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from config.settings import config
from config.database import db
from werkzeug.security import generate_password_hash
from typing import Dict, Any, Optional, cast

def apply_migrations():
    """Apply database migrations."""
    print("\n=== Checking Database Schema ===")
    
    with db.get_cursor() as cursor:
        # Check if admin_users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'admin_users'
            ) as exists
        """)
        result = cast(Optional[Dict[str, Any]], cursor.fetchone())
        admin_table_exists = result['exists'] if result else False
        
        if not admin_table_exists:
            print("Admin users table not found. Applying migrations...")
            
            # Read and execute migration file
            migration_file = os.path.join(os.path.dirname(__file__), 'migrations', '002_add_admin_users_and_rankedwar.sql')
            
            if os.path.exists(migration_file):
                with open(migration_file, 'r') as f:
                    migration_sql = f.read()
                    
                # Execute migration
                cursor.execute(migration_sql)
                print("[OK] Migrations applied successfully")
            else:
                print(f"[ERROR] Migration file not found: {migration_file}")
                print("\nYou need to manually apply the migration. Run:")
                print(f"  psql {config.POSTGRES_URL} -f backend/migrations/002_add_admin_users_and_rankedwar.sql")
                return False
        else:
            print("[OK] Database schema is up to date")
    
    return True

def validate_torn_user(username, api_key):
    """Validate username and get Torn ID using API key."""
    try:
        response = requests.get(
            f'https://api.torn.com/v2/user?key={api_key}',
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"[ERROR] Torn API returned status {response.status_code}")
            return None
        
        data = response.json()
        
        if 'error' in data:
            print(f"[ERROR] Torn API error: {data['error'].get('error', 'Unknown error')}")
            return None
        
        profile = data.get('profile', {})
        torn_username = profile.get('name', '')
        torn_id = profile.get('id')
        faction_id = profile.get('faction_id')
        
        if torn_username != username:
            print(f"[ERROR] Username mismatch! Torn username is '{torn_username}', but you entered '{username}'")
            return None
        
        if not faction_id:
            print("[ERROR] Your Torn account is not in a faction. You must be in a faction to use this tool.")
            return None
        
        return {
            'torn_id': torn_id,
            'username': torn_username,
            'faction_id': faction_id
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to validate with Torn API: {e}")
        return None

def create_admin_user():
    """Create the initial admin user."""
    print("\n=== Create Your Admin Account ===")
    print("You'll need:")
    print("  1. Your Torn username (must match your Torn account exactly)")
    print("  2. A password for this tool (can be different from your Torn password)")
    print("  3. Your Torn API key (to verify your identity and faction)")
    print()
    
    # Get username
    username = input("Enter your Torn username: ").strip()
    if not username:
        print("[ERROR] Username cannot be empty")
        return False
    
    # Get password
    password = getpass("Enter a password for this tool: ")
    password_confirm = getpass("Confirm password: ")
    
    if password != password_confirm:
        print("[ERROR] Passwords do not match")
        return False
    
    if len(password) < 6:
        print("[ERROR] Password must be at least 6 characters")
        return False
    
    # Get API key
    api_key = getpass("Enter your Torn API key: ").strip()
    if not api_key:
        print("[ERROR] API key cannot be empty")
        return False
    
    # Validate with Torn API
    print("\nValidating with Torn API...")
    user_data = validate_torn_user(username, api_key)
    
    if not user_data:
        return False
    
    print(f"[OK] Validated: {user_data['username']} (ID: {user_data['torn_id']}, Faction: {user_data['faction_id']})")
    
    # Check if user already exists
    with db.get_cursor() as cursor:
        cursor.execute("SELECT admin_id FROM admin_users WHERE torn_id = %s", (user_data['torn_id'],))
        existing = cursor.fetchone()
        
        if existing:
            print(f"[ERROR] Admin user already exists with Torn ID {user_data['torn_id']}")
            return False
    
    # Create admin user
    password_hash = generate_password_hash(password)
    
    with db.get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO admin_users (torn_id, username, password_hash, faction_id)
            VALUES (%s, %s, %s, %s)
            RETURNING admin_id
        """, (user_data['torn_id'], user_data['username'], password_hash, user_data['faction_id']))
        
        result = cast(Optional[Dict[str, Any]], cursor.fetchone())
        admin_id = result['admin_id'] if result else None
        
        if admin_id:
            print(f"\n[OK] Admin account created successfully! (Admin ID: {admin_id})")
            print(f"\nYou can now login at http://localhost:3000 with:")
            print(f"  Username: {user_data['username']}")
            print(f"  Password: <the password you just set>")
            print(f"  API Key: <your Torn API key>")
            return True
        else:
            print("[ERROR] Failed to create admin account")
            return False

def main():
    """Main setup function."""
    print("=== Torn War Calculator - Admin Setup ===")
    print(f"Database: {config.POSTGRES_URL}")
    print()
    
    # Test database connection
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            print("[OK] Database connection successful")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database exists")
        print("  3. Connection string in .env is correct")
        return 1
    
    # Apply migrations if needed
    if not apply_migrations():
        return 1
    
    # Create admin user
    if not create_admin_user():
        return 1
    
    print("\n=== Setup Complete ===")
    print("You can now start using the Torn War Calculator!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
