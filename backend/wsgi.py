"""WSGI entry point for the application."""
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import from application module (not app to avoid directory conflict)
from application import create_app

# Create the application
application = create_app()

if __name__ == '__main__':
    application.run()
