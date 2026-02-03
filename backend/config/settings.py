"""Configuration settings for the application."""
import os
from datetime import timedelta
from dotenv import load_dotenv
from pathlib import Path

# Get the backend directory path and load .env files from there
backend_dir = Path(__file__).parent.parent
# Load .env first (defaults), then .env.local (overrides)
load_dotenv(dotenv_path=backend_dir / '.env')
load_dotenv(dotenv_path=backend_dir / '.env.local', override=True)

class Config:
    """Base configuration class."""
    
    # Database
    POSTGRES_URL = os.getenv('POSTGRES_URL')
    
    # Security
    ENCRYPTION_MASTER_KEY = os.getenv('ENCRYPTION_MASTER_KEY')
    JWT_SECRET = os.getenv('JWT_SECRET')
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Torn API
    TORN_API_BASE_URL = os.getenv('TORN_API_BASE_URL', 'https://api.torn.com/v2')
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 80))
    
    # Flask
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', 30))
    ACCESS_TOKEN_EXPIRY_HOURS = int(os.getenv('ACCESS_TOKEN_EXPIRY_HOURS', 24))
    REFRESH_TOKEN_EXPIRY_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRY_DAYS', 7))
    
    # Audit Log Retention
    AUDIT_LOG_RETENTION_DAYS = int(os.getenv('AUDIT_LOG_RETENTION_DAYS', 30))
    
    # CORS
    cors_env = os.getenv('CORS_ORIGINS', '')
    default_origins = [
        'https://toolboxfront-grz8mw1lw-reddragons-projects-4bb4edcd.vercel.app',
        'https://thc-toolbox-frontend.vercel.app',
        'https://thc-toolbox.vercel.app',
        'http://localhost:3000',
        'http://localhost:3001',
        'http://localhost:3002'
    ]
    if cors_env:
        env_origins = [origin.strip() for origin in cors_env.split(',') if origin.strip()]
        # Always merge defaults to avoid accidental production lockout
        merged = list(dict.fromkeys(env_origins + default_origins))
        CORS_ORIGINS = merged
    else:
        # Fallback: support both old and new frontend URLs
        CORS_ORIGINS = default_origins
    
    @staticmethod
    def validate():
        """Validate required environment variables."""
        required_vars = [
            'POSTGRES_URL',
            'ENCRYPTION_MASTER_KEY',
            'JWT_SECRET'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

config = Config()
