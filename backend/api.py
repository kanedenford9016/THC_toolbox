import sys
from pathlib import Path
import os

# Add backend to path BEFORE importing anything else
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set env var for non-blocking startup
os.environ.setdefault('FLASK_ENV', os.getenv('FLASK_ENV', 'production'))

# Now import - this will be the serverless entry point
from app import create_app

app = create_app()
