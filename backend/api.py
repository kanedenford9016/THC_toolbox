import sys
from pathlib import Path
import os
import importlib.util

# Add backend to path BEFORE importing anything else
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set env var for non-blocking startup
os.environ.setdefault('FLASK_ENV', os.getenv('FLASK_ENV', 'production'))

# Load app.py explicitly by file path to avoid name conflicts with app/ directory
app_py_path = backend_dir / 'app.py'
spec = importlib.util.spec_from_file_location("app_module", app_py_path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

# Get the create_app function
create_app = app_module.create_app

# Create the Flask app instance
app = create_app()
