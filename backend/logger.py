import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from functools import wraps
from flask import request, session
import time
import json

class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        return super().format(record)

def setup_logger(name='app', log_dir='logs'):
    """Setup application logger with file and console handlers"""

    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler - All logs
    all_log_file = os.path.join(log_dir, 'all.log')
    file_handler_all = RotatingFileHandler(
        all_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler_all.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler_all.setFormatter(file_formatter)
    logger.addHandler(file_handler_all)

    # File handler - Errors only
    error_log_file = os.path.join(log_dir, 'errors.log')
    file_handler_error = RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler_error.setLevel(logging.ERROR)
    file_handler_error.setFormatter(file_formatter)
    logger.addHandler(file_handler_error)

    # File handler - API requests
    api_log_file = os.path.join(log_dir, 'api_requests.log')
    file_handler_api = RotatingFileHandler(
        api_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler_api.setLevel(logging.INFO)
    api_formatter = logging.Formatter(
        '%(asctime)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler_api.setFormatter(api_formatter)

    # Console handler - with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger, file_handler_api

# Initialize logger
logger, api_file_handler = setup_logger()

def get_user_info():
    """Get current user information from session"""
    if 'user_id' in session:
        return {
            'user_id': session.get('user_id'),
            'email': session.get('email'),
            'role': session.get('role')
        }
    return {'user_id': None, 'email': 'anonymous', 'role': 'guest'}

def log_request_info():
    """Log incoming request information"""
    user_info = get_user_info()

    log_data = {
        'method': request.method,
        'path': request.path,
        'user': user_info['email'],
        'role': user_info['role'],
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')[:50]
    }

    # Log request body for POST/PUT (exclude sensitive data)
    if request.method in ['POST', 'PUT', 'PATCH']:
        try:
            data = request.get_json() or {}
            # Remove sensitive fields
            safe_data = {k: v for k, v in data.items() if k not in ['password', 'hashed_password']}
            if safe_data:
                log_data['data'] = safe_data
        except:
            pass

    return log_data

def log_api_call(func):
    """Decorator to log API endpoint calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        user_info = get_user_info()

        # Log request
        logger.info(f"→ {request.method} {request.path} | User: {user_info['email']} ({user_info['role']})")

        try:
            # Execute the function
            result = func(*args, **kwargs)

            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # ms

            # Log successful response
            status_code = 200
            if isinstance(result, tuple):
                status_code = result[1] if len(result) > 1 else 200

            logger.info(f"← {request.method} {request.path} | Status: {status_code} | Time: {execution_time:.2f}ms")

            # Log to API file
            api_logger = logging.getLogger('api')
            api_logger.addHandler(api_file_handler)
            api_logger.info(
                f"{request.method} {request.path} | User: {user_info['email']} | "
                f"Status: {status_code} | Time: {execution_time:.2f}ms"
            )

            return result

        except Exception as e:
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # ms

            # Log error
            logger.error(
                f"✗ {request.method} {request.path} | User: {user_info['email']} | "
                f"Error: {str(e)} | Time: {execution_time:.2f}ms"
            )
            logger.exception("Exception details:")

            # Log to API file
            api_logger = logging.getLogger('api')
            api_logger.addHandler(api_file_handler)
            api_logger.error(
                f"{request.method} {request.path} | User: {user_info['email']} | "
                f"Error: {str(e)} | Time: {execution_time:.2f}ms"
            )

            raise

    return wrapper

def log_database_operation(operation, table, details=None):
    """Log database operations"""
    user_info = get_user_info()
    msg = f"DB: {operation} on {table}"
    if details:
        msg += f" | {details}"
    msg += f" | User: {user_info['email']}"
    logger.debug(msg)

def log_authentication(action, email, success, reason=None):
    """Log authentication attempts"""
    status = "SUCCESS" if success else "FAILED"
    msg = f"AUTH: {action} | Email: {email} | Status: {status}"
    if reason:
        msg += f" | Reason: {reason}"

    if success:
        logger.info(msg)
    else:
        logger.warning(msg)

def log_file_operation(operation, filename, details=None):
    """Log file operations"""
    user_info = get_user_info()
    msg = f"FILE: {operation} | File: {filename}"
    if details:
        msg += f" | {details}"
    msg += f" | User: {user_info['email']}"
    logger.info(msg)

def log_course_operation(operation, course_id, course_title=None, details=None):
    """Log course operations"""
    user_info = get_user_info()
    msg = f"COURSE: {operation} | ID: {course_id}"
    if course_title:
        msg += f" | Title: {course_title}"
    if details:
        msg += f" | {details}"
    msg += f" | User: {user_info['email']}"
    logger.info(msg)

def log_assignment_operation(course_id, student_ids, action='assign'):
    """Log course assignment operations"""
    user_info = get_user_info()
    msg = f"ASSIGNMENT: {action.upper()} | Course ID: {course_id} | Students: {len(student_ids)} | Admin: {user_info['email']}"
    logger.info(msg)

def log_session_activity(action, details=None):
    """Log session activities"""
    user_info = get_user_info()
    msg = f"SESSION: {action} | User: {user_info['email']}"
    if details:
        msg += f" | {details}"
    logger.info(msg)

# Log startup
logger.info("=" * 80)
logger.info("APPLICATION STARTING")
logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info(f"Log Directory: logs/")
logger.info("=" * 80)
