from functools import wraps
from flask import session, jsonify
from werkzeug.security import check_password_hash
from backend.database import get_connection, use_postgres, execute_query
from backend.logger import logger
import os

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        if session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def verify_user(email, password):
    """Verify user credentials and return user data if valid"""
    try:
        result = execute_query(
            'SELECT id, email, hashed_password, role FROM users WHERE email = %s',
            [email], 
            fetch_one=True
        )

        if result and check_password_hash(result['hashed_password'], password):
            logger.info(f"User authentication successful: {email}")
            return {
                'id': result['id'],
                'email': result['email'],
                'role': result['role']
            }
        else:
            logger.warning(f"User authentication failed: {email} - {'User not found' if not result else 'Invalid password'}")
            return None
            
    except Exception as e:
        logger.error(f"Authentication error for {email}: {str(e)}")
        return None

def get_current_user():
    """Get current logged-in user data from session"""
    if 'user_id' not in session:
        return None

    try:
        result = execute_query(
            'SELECT id, email, role FROM users WHERE id = %s',
            [session['user_id']],
            fetch_one=True
        )

        if result:
            return {
                'id': result['id'],
                'email': result['email'],
                'role': result['role']
            }
        else:
            logger.warning(f"User not found for session user_id: {session['user_id']}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return None
