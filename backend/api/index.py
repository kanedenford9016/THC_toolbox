"""Vercel serverless handler."""
import sys
from pathlib import Path
import os

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set environment
os.environ.setdefault('FLASK_ENV', os.getenv('FLASK_ENV', 'production'))

# Import app
from app import create_app

app = create_app()

def handler(request):
    """Vercel serverless handler."""
    return app(request)
