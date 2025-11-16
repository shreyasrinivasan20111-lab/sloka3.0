from functools import wraps
from flask import session, jsonify
from werkzeug.security import check_password_hash
from backend.database import get_connection

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
    conn = get_connection()
    result = conn.execute(
        'SELECT id, email, hashed_password, role FROM users WHERE email = ?',
        [email]
    ).fetchone()
    conn.close()

    if result and check_password_hash(result[2], password):
        return {
            'id': result[0],
            'email': result[1],
            'role': result[3]
        }
    return None

def get_current_user():
    """Get current logged-in user data from session"""
    if 'user_id' not in session:
        return None

    conn = get_connection()
    result = conn.execute(
        'SELECT id, email, role FROM users WHERE id = ?',
        [session['user_id']]
    ).fetchone()
    conn.close()

    if result:
        return {
            'id': result[0],
            'email': result[1],
            'role': result[2]
        }
    return None
