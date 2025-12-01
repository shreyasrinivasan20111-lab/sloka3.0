import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in development
load_dotenv()

class Config:
    """Base configuration"""
    # Secret key for sessions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database configuration
    # In serverless environments, use memory database or persistent storage
    if os.environ.get('VERCEL') == '1':
        # For Vercel, use a persistent database path in /tmp (which persists during function execution)
        DB_PATH = os.environ.get('DB_PATH') or '/tmp/student_courses.db'
        UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or '/tmp/uploads'
    else:
        # For local development, use relative paths
        DB_PATH = os.environ.get('DB_PATH') or 'student_courses.db'
        UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'gif', 'zip'}

    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

    # Flask settings
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    CORS_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

    # In production, SECRET_KEY should be set via environment variable
    # Falls back to a warning message if not set
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'INSECURE-CHANGE-THIS-IN-PRODUCTION'

    # For Vercel/serverless, use /tmp directory
    if os.environ.get('VERCEL'):
        DB_PATH = '/tmp/student_courses.db'
        UPLOAD_FOLDER = '/tmp/uploads'

    # Allow all origins in production (or specify your domain)
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DB_PATH = ':memory:'  # In-memory database for tests

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
