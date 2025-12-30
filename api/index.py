import os
import sys

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set serverless environment flag
os.environ['VERCEL'] = '1'

# Import the Flask application
from backend.app import app
from backend.database import init_database
from backend.logger import logger

# Initialize database on cold start with comprehensive serverless fixes
try:
    logger.info("🚀 VERCEL COLD START: Initializing database...")
    
    # Initialize database tables
    init_database()
    logger.info("✅ Database tables initialized")
    
    logger.info("✅ Server initialization complete")
    
    logger.info("🎉 VERCEL INITIALIZATION COMPLETE")
    
except Exception as e:
    logger.error(f"❌ Database initialization error: {str(e)}")
    # Continue anyway - the app might still work with existing database
