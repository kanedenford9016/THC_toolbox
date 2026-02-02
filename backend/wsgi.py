"""WSGI entry point for the application."""
import sys
from pathlib import Path
import importlib.util

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load app.py explicitly to avoid package/module name conflict
app_py_path = backend_dir / 'app.py'
spec = importlib.util.spec_from_file_location("app_module", app_py_path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

# Create the application
application = app_module.create_app()

if __name__ == '__main__':
    application.run()
