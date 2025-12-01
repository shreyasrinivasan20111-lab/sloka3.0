import os
import sys

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set serverless environment flag
os.environ['VERCEL'] = '1'

# Import the Flask application
from backend.app import app
from backend.database import init_database

# Initialize database on cold start
try:
    init_database()
except Exception as e:
    # Don't fail deployment if database already exists
    pass
