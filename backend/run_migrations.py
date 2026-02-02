import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def run_migrations():
    db_url = os.getenv('POSTGRES_URL')
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    migration_dir = Path(__file__).parent / 'migrations'
    migration_files = sorted(migration_dir.glob('*.sql'))
    
    for migration_file in migration_files:
        print(f"Running {migration_file.name}...")
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        try:
            cursor.execute(sql)
            conn.commit()
            print(f"✓ {migration_file.name} completed")
        except Exception as e:
            print(f"✗ {migration_file.name} failed: {e}")
            conn.rollback()
    
    cursor.close()
    conn.close()
    print("All migrations completed!")

if __name__ == '__main__':
    run_migrations()
