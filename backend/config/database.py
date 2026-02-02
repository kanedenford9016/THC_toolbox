"""Database connection and operations."""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config.settings import config
from urllib.parse import urlparse

class Database:
    """Database connection manager."""
    
    @staticmethod
    def _parse_db_url(url):
        """Parse database URL into connection parameters."""
        parsed = urlparse(url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'user': parsed.username,
            'password': parsed.password
        }
    
    @staticmethod
    @contextmanager
    def get_connection():
        """Get a database connection with context manager."""
        conn = None
        try:
            # Parse the URL and connect with explicit parameters
            conn_params = Database._parse_db_url(config.POSTGRES_URL)
            conn = psycopg2.connect(
                host=conn_params['host'],
                port=conn_params['port'],
                database=conn_params['database'],
                user=conn_params['user'],
                password=conn_params['password'],
                cursor_factory=RealDictCursor
            )
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    @contextmanager
    def get_cursor():
        """Get a database cursor with context manager."""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

db = Database()
