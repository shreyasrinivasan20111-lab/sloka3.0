"""
Vercel serverless function entry point
This file adapts the Flask app to work with Vercel's serverless architecture
"""

import os
import sys

# Add parent directory to path so we can import backend module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment to production for Vercel
os.environ['FLASK_ENV'] = 'production'
os.environ['VERCEL'] = '1'

from backend.app import app
from backend.database import init_database

# Initialize database on cold start
try:
    init_database()
except Exception as e:
    print(f"Database initialization warning: {e}")
    # Continue even if database init fails (might already exist)

# Vercel will call this handler
def handler(request, context):
    """Vercel serverless handler"""
    return app(request, context)

# For local testing and compatibility
if __name__ == "__main__":
    app.run(debug=False)
