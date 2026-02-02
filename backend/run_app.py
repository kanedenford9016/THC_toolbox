#!/usr/bin/env python3
"""Run the Flask app directly."""
import sys
sys.path.insert(0, '.')

from api import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
