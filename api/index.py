import os
import sys

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set serverless environment flag
os.environ['VERCEL'] = '1'

# Import the Flask application
from backend.app import app
from backend.database_unified import init_database
from backend.logger import logger

# Initialize database on cold start with comprehensive serverless fixes
try:
    logger.info("🚀 VERCEL COLD START: Initializing database...")
    
    # Initialize database tables
    init_database()
    logger.info("✅ Database tables initialized")
    
    # SERVERLESS FIX: Restore users from JSON backup if database is empty
    try:
        from backend.database_unified import get_connection
        from backend.json_storage import restore_from_json_backup
        
        conn = get_connection()
        user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        conn.close()
        
        if user_count == 0:
            logger.info("📥 Database is empty, attempting to restore from JSON backup...")
            restored_count = restore_from_json_backup()
            if restored_count > 0:
                logger.info(f"✅ Restored {restored_count} users from JSON backup")
            else:
                logger.info("ℹ️ No JSON backup found or backup was empty")
        else:
            logger.info(f"✅ Database already has {user_count} users")
            
    except Exception as restore_error:
        logger.warning(f"⚠️ JSON backup restoration failed: {str(restore_error)}")
        # Continue anyway - the app should still work for new signups
        
    logger.info("🎉 VERCEL INITIALIZATION COMPLETE")
    
except Exception as e:
    logger.error(f"❌ Database initialization error: {str(e)}")
    # Continue anyway - the app might still work with existing database
