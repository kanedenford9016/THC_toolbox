import sys
from pathlib import Path
import os

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment
os.environ.setdefault('FLASK_ENV', os.getenv('FLASK_ENV', 'production'))

# Import from application module (not app to avoid directory conflict)
from application import create_app

# Create Flask app for Vercel
app = create_app()
