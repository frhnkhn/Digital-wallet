"""
Vercel Serverless Function Entry Point
Wraps the Flask app as a WSGI handler for Vercel's Python runtime.
Auto-seeds the database on cold start since Vercel uses ephemeral /tmp storage.
"""

import sys
import os

# Add backend_python to Python path
_backend = os.path.join(os.path.dirname(__file__), '..', 'backend_python')
sys.path.insert(0, os.path.abspath(_backend))

# Auto-seed on cold start (Vercel /tmp is ephemeral)
from database import DB_PATH, init_db

if not os.path.exists(DB_PATH):
    init_db()
    from seed_data import seed
    seed()

# Import the Flask app (this also initializes routes, blueprints, etc.)
from app import app
