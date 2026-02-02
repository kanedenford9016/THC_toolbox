"""Vercel serverless entry point - passthrough to api.py."""
import sys
from pathlib import Path
import os

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from api import app

# Vercel routes all requests through this file
if __name__ == '__main__':
    app.run()
