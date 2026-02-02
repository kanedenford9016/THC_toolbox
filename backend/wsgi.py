"""WSGI entry point for the application."""
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import the create_app function - note: we're importing directly from app.py which is in the same directory
import app as app_module

# Create the application
application = app_module.create_app()

if __name__ == '__main__':
    application.run()
