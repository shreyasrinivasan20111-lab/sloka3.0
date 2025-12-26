from flask import Flask, request, jsonify, session, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import time
import json
from backend.database_unified import get_connection, init_database, use_postgres
from backend.auth import login_required, admin_required, verify_user, get_current_user
from backend.config import get_config
from backend.logger import (
    logger,
    log_api_call,
    log_authentication,
    log_database_operation,
    log_file_operation,
    log_course_operation,
    log_assignment_operation,
    log_session_activity,
    get_user_info
)
from backend.json_storage import (
    backup_courses_to_json,
    backup_all_to_json,
    get_json_backup_status,
    sync_course_to_json,
    backup_assignments_to_json
)

# Get configuration
config = get_config()

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config.from_object(config)
app.secret_key = config.SECRET_KEY

logger.info(f"Flask app initialized | Config: {config.__class__.__name__}")

# Configure CORS
CORS(app,
     origins=config.CORS_ORIGINS,
     supports_credentials=True,
     allow_headers=['Content-Type'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

logger.info(f"CORS configured | Origins: {config.CORS_ORIGINS}")

# Create upload folder
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
logger.info(f"Upload folder ready: {config.UPLOAD_FOLDER}")

# ============= Middleware =============

@app.before_request
def before_request():
    """Log all incoming requests"""
    try:
        request.start_time = time.time()

        # Don't log static file requests
        if request.path.startswith('/static') or request.path.endswith(('.css', '.js', '.png', '.jpg', '.ico')):
            return

        # Get user info safely
        try:
            user_info = get_user_info()
            user_email = user_info.get('email', 'unknown')
        except:
            user_email = 'unknown'
            
        logger.debug(f"→ {request.method} {request.path} | User: {user_email} | IP: {request.remote_addr}")
    except Exception as e:
        # Don't let middleware errors break the request
        print(f"Before request middleware error: {str(e)}")
        request.start_time = time.time()  # Ensure this is set
        pass

@app.after_request
def after_request(response):
    """Log all outgoing responses"""
    try:
        # Don't log static file requests
        if request.path.startswith('/static') or request.path.endswith(('.css', '.js', '.png', '.jpg', '.ico')):
            return response

        # Calculate request duration
        if hasattr(request, 'start_time'):
            duration = (time.time() - request.start_time) * 1000  # Convert to ms
            
            # Get user info safely
            try:
                user_info = get_user_info()
                user_email = user_info.get('email', 'unknown')
            except:
                user_email = 'unknown'

            log_level = logger.info if response.status_code < 400 else logger.error
            log_level(
                f"← {request.method} {request.path} | "
                f"Status: {response.status_code} | "
                f"User: {user_email} | "
                f"Time: {duration:.2f}ms"
            )
    except Exception as e:
        # Don't let middleware errors break the response
        print(f"Middleware error: {str(e)}")
        pass

    return response

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

# ============= Authentication Endpoints =============

@app.route('/api/login', methods=['POST'])
def login():
    """Enhanced login with serverless database persistence fixes"""
    try:
        data = request.json
        if not data:
            logger.warning("Login failed: No JSON data provided")
            return jsonify({'error': 'No data provided'}), 400
            
        email = data.get('email')
        password = data.get('password')

        logger.info(f"Login attempt for email: {email}")

        if not email or not password:
            logger.warning(f"Login failed: Missing credentials | Email: {email}")
            return jsonify({'error': 'Email and password required'}), 400

        # SERVERLESS FIX: Ensure database is initialized before auth
        try:
            from backend.database_unified import ensure_tables_exist
            ensure_tables_exist()
            logger.info("Database tables verified for login")
        except Exception as db_error:
            logger.error(f"Database initialization failed during login: {str(db_error)}")
            return jsonify({'error': 'Service temporarily unavailable'}), 503

        user = verify_user(email, password)
        if user:
            # Clear any existing session first
            session.clear()
            
            session['user_id'] = user['id']
            session['email'] = user['email']
            session['role'] = user['role']
            session.permanent = True

            # Verify session was set correctly (serverless protection)
            if session.get('user_id') != user['id']:
                logger.error(f"Session verification failed for {email}")
                return jsonify({'error': 'Login failed due to session error'}), 500

            log_authentication('LOGIN', email, True)
            log_session_activity('START', f"User ID: {user['id']}, Role: {user['role']}")
            logger.info(f"✓ Login successful | User: {email} | Role: {user['role']} | ID: {user['id']}")

            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'role': user['role']
                }
            })
        else:
            log_authentication('LOGIN', email, False, 'Invalid credentials')
            logger.warning(f"✗ Login failed: Invalid credentials | Email: {email}")
            return jsonify({'error': 'Invalid credentials'}), 401
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error during login'}), 500

@app.route('/api/signup', methods=['POST'])
def signup():
    """Enhanced signup with serverless database persistence fixes"""
    try:
        data = request.json
        if not data:
            logger.warning("Signup failed: No JSON data provided")
            return jsonify({'error': 'No data provided'}), 400
            
        email = data.get('email')
        password = data.get('password')

        logger.info(f"Signup attempt for email: {email}")

        if not email or not password:
            logger.warning(f"Signup failed: Missing credentials | Email: {email}")
            return jsonify({'error': 'Email and password required'}), 400

        # Basic email validation
        if '@' not in email or '.' not in email:
            logger.warning(f"Signup failed: Invalid email format | Email: {email}")
            return jsonify({'error': 'Invalid email format'}), 400

        # SERVERLESS FIX: Ensure database is initialized before any operations
        try:
            from backend.database_unified import ensure_tables_exist
            ensure_tables_exist()
            logger.info("Database tables verified for signup")
        except Exception as db_error:
            logger.error(f"Database initialization failed during signup: {str(db_error)}")
            return jsonify({'error': 'Service temporarily unavailable'}), 503

        # Check if email already exists
        conn = get_connection()
        log_database_operation('SELECT', 'users', f'Check existing email: {email}')
        existing = conn.execute('SELECT id FROM users WHERE email = ?', [email]).fetchone()
        if existing:
            conn.close()
            log_authentication('SIGNUP', email, False, 'Email already registered')
            logger.warning(f"✗ Signup failed: Email already exists | Email: {email}")
            return jsonify({'error': 'Email already registered'}), 400

        # Create new student account
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        log_database_operation('INSERT', 'users', f'New student account: {email}')
        
        # Check if we're using PostgreSQL or DuckDB for proper ID handling
        from backend.database_unified import use_postgres
        if use_postgres():
            conn.execute('''
                INSERT INTO users (id, email, hashed_password, role)
                VALUES (nextval('users_id_seq'), ?, ?, 'student')
            ''', [email, hashed_password])
        else:
            # DuckDB - calculate next ID manually
            max_id_result = conn.execute('SELECT COALESCE(MAX(id), 0) FROM users').fetchone()
            next_id = (max_id_result[0] if max_id_result else 0) + 1
            
            conn.execute('''
                INSERT INTO users (id, email, hashed_password, role)
                VALUES (?, ?, ?, 'student')
            ''', [next_id, email, hashed_password])
        
        conn.commit()

        # Get the new user ID
        user_id = conn.execute('SELECT MAX(id) FROM users').fetchone()[0]
        
        # SERVERLESS FIX: Force JSON backup immediately after signup
        try:
            from backend.json_storage import backup_all_to_json
            backup_all_to_json()
            logger.info(f"JSON backup completed after signup for {email}")
        except Exception as backup_error:
            logger.warning(f"JSON backup failed after signup: {str(backup_error)}")
        
        conn.close()

        # Clear any existing session first, then auto-login after signup
        session.clear()
        session['user_id'] = user_id
        session['email'] = email
        session['role'] = 'student'
        session.permanent = True

        # Verify session was set correctly (serverless protection)
        if session.get('user_id') != user_id:
            logger.error(f"Session verification failed after signup for {email}")
            return jsonify({'error': 'Account created but login failed'}), 500

        log_authentication('SIGNUP', email, True)
        log_session_activity('START', f"New student account | User ID: {user_id}")
        logger.info(f"✓ Signup successful | User: {email} | ID: {user_id} | Auto-logged in")

        return jsonify({
            'message': 'Account created successfully',
            'user': {
                'id': user_id,
                'email': email,
                'role': 'student'
            }
        }), 201
    
    except Exception as e:
        logger.error(f"Signup error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error during signup'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        user_info = get_user_info()
        logger.info(f"Logout request | User: {user_info['email']}")

        log_session_activity('END', f"User logged out")
        session.clear()

        logger.info(f"✓ Logout successful | User: {user_info['email']}")
        return jsonify({'message': 'Logged out successfully'})
    
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        # Still clear session even if logging fails
        try:
            session.clear()
        except:
            pass
        return jsonify({'message': 'Logged out successfully'})

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated - Ultra-robust version with serverless fixes"""
    response_data = {'authenticated': False}
    
    try:
        # Check if Flask session object exists
        if not hasattr(request, 'environ') or session is None:
            return jsonify(response_data), 200
        
        # Safely check session contents
        session_dict = None
        try:
            session_dict = dict(session)
        except:
            return jsonify(response_data), 200
        
        # Check if user_id exists in session
        if not session_dict or 'user_id' not in session_dict:
            return jsonify(response_data), 200
        
        # Extract values with multiple fallbacks
        user_id = None
        email = None
        role = None
        
        try:
            user_id = session_dict.get('user_id')
            email = session_dict.get('email') 
            role = session_dict.get('role')
        except:
            return jsonify(response_data), 200
        
        # Validate all required fields exist and are not None/empty
        if not user_id or not email or not role:
            try:
                session.clear()
            except:
                pass
            return jsonify(response_data), 200
        
        # Convert and validate user_id
        try:
            if isinstance(user_id, str):
                if not user_id.strip().isdigit():
                    try:
                        session.clear()
                    except:
                        pass
                    return jsonify(response_data), 200
                user_id = int(user_id.strip())
            elif not isinstance(user_id, int):
                try:
                    session.clear()
                except:
                    pass
                return jsonify(response_data), 200
        except:
            try:
                session.clear()
            except:
                pass
            return jsonify(response_data), 200
        
        # Validate email format (basic check)
        try:
            email = str(email).strip()
            if not email or '@' not in email or len(email) < 3:
                try:
                    session.clear()
                except:
                    pass
                return jsonify(response_data), 200
        except:
            try:
                session.clear()
            except:
                pass
            return jsonify(response_data), 200
        
        # Validate role
        try:
            role = str(role).strip().lower()
            if role not in ['admin', 'student']:
                try:
                    session.clear()
                except:
                    pass
                return jsonify(response_data), 200
        except:
            try:
                session.clear()
            except:
                pass
            return jsonify(response_data), 200
        
        # SERVERLESS FIX: Verify user still exists in database
        # This is critical for serverless environments where DB might be recreated
        try:
            conn = get_connection()
            db_user = conn.execute(
                'SELECT id, email, role FROM users WHERE id = ? AND email = ?',
                [user_id, email]
            ).fetchone()
            conn.close()
            
            if not db_user:
                logger.warning(f"Session user not found in database (serverless restart?): {email} (ID: {user_id})")
                try:
                    session.clear()
                except:
                    pass
                return jsonify({
                    'authenticated': False,
                    'error': 'session_invalid',
                    'message': 'Session expired due to server restart. Please login again.'
                }), 200
                
            # Verify role matches
            if db_user[2].lower() != role:
                logger.warning(f"Role mismatch for user {email}: session={role}, db={db_user[2]}")
                try:
                    session.clear()
                except:
                    pass
                return jsonify(response_data), 200
                
        except Exception as e:
            logger.error(f"Database check error during auth validation: {str(e)}")
            # If DB check fails, clear session to be safe
            try:
                session.clear()
            except:
                pass
            return jsonify(response_data), 200
        
        # All validations passed - construct response safely
        try:
            response_data = {
                'authenticated': True,
                'user': {
                    'id': user_id,
                    'email': email,
                    'role': role
                }
            }
            return jsonify(response_data), 200
        except:
            return jsonify({'authenticated': False}), 200
    
    except Exception as e:
        # Ultimate fallback - log error safely and return unauthenticated
        try:
            import sys
            import traceback
            error_msg = f"Check-auth critical error: {str(e)}"
            print(error_msg, file=sys.stderr)
            print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        except:
            pass
        
        # Clear session as last resort
        try:
            if session:
                session.clear()
        except:
            pass
        
        # Return safe response
        return jsonify({'authenticated': False}), 200

@app.route('/api/check-auth-simple', methods=['GET'])
def check_auth_simple():
    """Ultra-simple auth check for debugging"""
    try:
        return jsonify({
            'authenticated': 'user_id' in session if session else False,
            'session_exists': session is not None,
            'debug': 'simple-endpoint-working'
        }), 200
    except:
        return jsonify({
            'authenticated': False,
            'session_exists': False,
            'debug': 'simple-endpoint-error'
        }), 200

@app.route('/api/debug-db', methods=['GET'])
def debug_db():
    """Debug database connectivity"""
    try:
        from backend.database import get_connection
        conn = get_connection()
        result = conn.execute('SELECT COUNT(*) FROM users').fetchone()
        conn.close()
        return jsonify({
            'db_working': True,
            'user_count': result[0] if result else 0,
            'debug': 'db-connection-ok'
        }), 200
    except Exception as e:
        return jsonify({
            'db_working': False,
            'error': str(e),
            'debug': 'db-connection-failed'
        }), 200

@app.route('/api/db-status', methods=['GET'])
@admin_required
def get_db_status():
    """Get database status and statistics (admin only)"""
    try:
        conn = get_connection()
        
        # Get database type info
        from backend.database_unified import use_postgres, use_persistent_duckdb
        
        # Get counts from all tables - handle both DuckDB and PostgreSQL
        if use_postgres():
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()['count']
            cursor.execute('SELECT COUNT(*) FROM courses')
            course_count = cursor.fetchone()['count']
            cursor.execute('SELECT COUNT(*) FROM assigned_courses')
            assignment_count = cursor.fetchone()['count']
            cursor.execute('SELECT COUNT(*) FROM files')
            file_count = cursor.fetchone()['count']
            cursor.close()
            
            db_type = "PostgreSQL (External)"
            db_path = os.environ.get('DATABASE_URL', 'Environment variable')
            db_exists = True
            db_size = "N/A (External Database)"
            persistent = True
            storage_info = {
                'type': 'external_postgres',
                'persistent': True,
                'sync_available': False
            }
            
        elif use_persistent_duckdb():
            user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            course_count = conn.execute('SELECT COUNT(*) FROM courses').fetchone()[0]
            assignment_count = conn.execute('SELECT COUNT(*) FROM assigned_courses').fetchone()[0]
            file_count = conn.execute('SELECT COUNT(*) FROM files').fetchone()[0]
            
            # Get persistent DuckDB storage info
            try:
                from backend.database_persistent import get_persistence_info
                storage_info = get_persistence_info()
                db_type = f"DuckDB ({storage_info['storage_type'].replace('_', ' ').title()})"
                db_path = storage_info['database_path']
                db_exists = storage_info['exists']
                db_size = f"{storage_info['size_mb']} MB"
                persistent = storage_info['is_persistent']
            except Exception as e:
                logger.warning(f"Failed to get persistent storage info: {e}")
                db_type = "DuckDB (Persistent - Error)"
                db_path = "Unknown"
                db_exists = False
                db_size = "Unknown"
                persistent = True
                storage_info = {'type': 'unknown', 'persistent': True}
            
        else:
            user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            course_count = conn.execute('SELECT COUNT(*) FROM courses').fetchone()[0]
            assignment_count = conn.execute('SELECT COUNT(*) FROM assigned_courses').fetchone()[0]
            file_count = conn.execute('SELECT COUNT(*) FROM files').fetchone()[0]
            
            from backend.config import get_config
            db_path = get_config().DB_PATH
            db_type = "DuckDB (Local)"
            db_exists = os.path.exists(db_path)
            db_size = f"{round(os.path.getsize(db_path) / 1024 / 1024, 2)} MB" if db_exists else "0 MB"
            persistent = not os.environ.get('VERCEL') == '1'
            storage_info = {
                'type': 'local_file',
                'persistent': persistent,
                'sync_available': False
            }
        
        conn.close()
        
        is_serverless = os.environ.get('VERCEL') == '1'
        
        # Determine status message
        if persistent:
            if use_postgres():
                status_msg = '✅ Data persists in external PostgreSQL database'
            elif use_persistent_duckdb():
                status_msg = '✅ Data persists with external DuckDB storage'
            else:
                status_msg = '✅ Data persists locally (development mode)'
        else:
            status_msg = '⚠️ Data will be lost on deployment restart'
        
        # Generate recommendations
        recommendations = []
        if not persistent:
            recommendations.append('Use PostgreSQL or persistent DuckDB for data persistence')
        if is_serverless and not use_postgres() and not use_persistent_duckdb():
            recommendations.append('Configure external storage for serverless deployment')
        if use_persistent_duckdb() and storage_info.get('cloud_sync_enabled'):
            recommendations.append('Automatic cloud sync is enabled')
        
        return jsonify({
            'database_type': db_type,
            'database_path': db_path,
            'database_exists': db_exists,
            'database_size': db_size,
            'is_serverless_env': is_serverless,
            'data_persistent': persistent,
            'storage_info': storage_info,
            'statistics': {
                'users': user_count,
                'courses': course_count,
                'assignments': assignment_count,
                'files': file_count
            },
            'status': status_msg,
            'recommendations': recommendations if recommendations else None
        })
        
    except Exception as e:
        logger.error(f"Database status error: {str(e)}")
        return jsonify({'error': f'Failed to get database status: {str(e)}'}), 500

@app.route('/api/db-sync', methods=['POST'])
@admin_required
def sync_database():
    """Manually sync database to cloud storage (admin only)"""
    try:
        from backend.database_unified import use_persistent_duckdb
        
        if not use_persistent_duckdb():
            return jsonify({
                'error': 'Database sync only available with persistent DuckDB storage',
                'current_storage': 'PostgreSQL' if use_postgres() else 'Local DuckDB'
            }), 400
        
        # Attempt to sync
        from backend.database_persistent import sync_database as do_sync
        success = do_sync()
        
        if success:
            logger.info("Manual database sync completed successfully")
            return jsonify({
                'message': 'Database synced successfully to cloud storage',
                'synced_at': time.time()
            })
        else:
            return jsonify({
                'error': 'Database sync failed - check cloud storage configuration',
                'help': 'Ensure BLOB_READ_WRITE_TOKEN or other cloud credentials are set'
            }), 500
            
    except ImportError:
        return jsonify({
            'error': 'Persistent database module not available'
        }), 500
    except Exception as e:
        logger.error(f"Database sync error: {str(e)}")
        return jsonify({
            'error': f'Database sync failed: {str(e)}'
        }), 500

@app.route('/api/me', methods=['GET'])
@login_required
def get_me():
    user = get_current_user()
    return jsonify({'user': user})

# ============= JSON Backup Endpoints =============

@app.route('/api/backup/json/status', methods=['GET'])
@admin_required
def get_json_backup_status_endpoint():
    """Get status of JSON backup files (admin only)"""
    try:
        status = get_json_backup_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"JSON backup status error: {str(e)}")
        return jsonify({'error': f'Failed to get JSON backup status: {str(e)}'}), 500

@app.route('/api/backup/json/courses', methods=['POST'])
@admin_required
def backup_courses_json_endpoint():
    """Manually backup courses to JSON (admin only)"""
    try:
        success = backup_courses_to_json()
        if success:
            return jsonify({
                'message': 'Courses backed up to JSON successfully',
                'timestamp': time.time()
            })
        else:
            return jsonify({'error': 'Failed to backup courses to JSON'}), 500
    except Exception as e:
        logger.error(f"JSON courses backup error: {str(e)}")
        return jsonify({'error': f'Failed to backup courses: {str(e)}'}), 500

@app.route('/api/backup/json/all', methods=['POST'])
@admin_required
def backup_all_json_endpoint():
    """Manually backup all data to JSON (admin only)"""
    try:
        success = backup_all_to_json()
        if success:
            return jsonify({
                'message': 'All data backed up to JSON successfully',
                'timestamp': time.time()
            })
        else:
            return jsonify({'error': 'Some JSON backups failed - check logs'}), 500
    except Exception as e:
        logger.error(f"JSON full backup error: {str(e)}")
        return jsonify({'error': f'Failed to backup all data: {str(e)}'}), 500

@app.route('/api/backup/json/download/<filename>', methods=['GET'])
@admin_required
def download_json_backup(filename):
    """Download JSON backup file (admin only)"""
    try:
        # Validate filename for security
        allowed_files = ['courses.json', 'users.json', 'assignments.json', 'files.json']
        if filename not in allowed_files:
            return jsonify({'error': 'Invalid backup file requested'}), 400
        
        from backend.json_storage import get_json_file_path
        file_path = get_json_file_path(filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Backup file not found'}), 404
        
        return send_file(
            file_path, 
            as_attachment=True, 
            download_name=f"backup_{filename}",
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"JSON backup download error: {str(e)}")
        return jsonify({'error': f'Failed to download backup: {str(e)}'}), 500

# ============= Admin Data Viewer Endpoints =============

@app.route('/api/admin/data/users', methods=['GET'])
@admin_required
def get_all_users_admin():
    """Get all users for admin data viewer (admin only)"""
    try:
        conn = get_connection()
        users = conn.execute('''
            SELECT id, email, role, created_at
            FROM users
            ORDER BY id
        ''').fetchall()
        
        result = []
        for user in users:
            result.append({
                'id': user[0],
                'email': user[1],
                'role': user[2],
                'created_at': str(user[3]) if user[3] else None
            })
        
        conn.close()
        return jsonify({'users': result})
        
    except Exception as e:
        logger.error(f"Admin users data error: {str(e)}")
        return jsonify({'error': f'Failed to get users data: {str(e)}'}), 500

@app.route('/api/admin/data/assignments', methods=['GET'])
@admin_required
def get_all_assignments_admin():
    """Get all assignments for admin data viewer (admin only)"""
    try:
        conn = get_connection()
        assignments = conn.execute('''
            SELECT ac.id, ac.user_id, ac.course_id, u.email, c.title
            FROM assigned_courses ac
            JOIN users u ON ac.user_id = u.id
            JOIN courses c ON ac.course_id = c.id
            ORDER BY ac.id
        ''').fetchall()
        
        result = []
        for assignment in assignments:
            result.append({
                'id': assignment[0],
                'user_id': assignment[1],
                'course_id': assignment[2],
                'user_email': assignment[3],
                'course_title': assignment[4]
            })
        
        conn.close()
        return jsonify({'assignments': result})
        
    except Exception as e:
        logger.error(f"Admin assignments data error: {str(e)}")
        return jsonify({'error': f'Failed to get assignments data: {str(e)}'}), 500

@app.route('/api/admin/data/files', methods=['GET'])
@admin_required
def get_all_files_admin():
    """Get all files for admin data viewer (admin only)"""
    try:
        conn = get_connection()
        files = conn.execute('''
            SELECT f.id, f.course_id, f.filename, f.file_path, c.title
            FROM files f
            JOIN courses c ON f.course_id = c.id
            ORDER BY f.id
        ''').fetchall()
        
        result = []
        for file in files:
            # Check if file exists and get size
            file_exists = os.path.exists(file[3]) if file[3] else False
            file_size = os.path.getsize(file[3]) if file_exists else 0
            
            result.append({
                'id': file[0],
                'course_id': file[1],
                'filename': file[2],
                'file_path': file[3],
                'course_title': file[4],
                'file_exists': file_exists,
                'file_size_bytes': file_size
            })
        
        conn.close()
        return jsonify({'files': result})
        
    except Exception as e:
        logger.error(f"Admin files data error: {str(e)}")
        return jsonify({'error': f'Failed to get files data: {str(e)}'}), 500

@app.route('/api/admin/json/<filename>', methods=['GET'])
@admin_required
def get_json_data_admin(filename):
    """Get JSON backup data for admin viewer (admin only)"""
    try:
        # Validate filename
        allowed_files = ['courses', 'users', 'assignments', 'files']
        if filename not in allowed_files:
            return jsonify({'error': 'Invalid JSON file requested'}), 400
        
        from backend.json_storage import get_json_file_path
        json_filename = f"{filename}.json"
        file_path = get_json_file_path(json_filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': f'JSON file {json_filename} not found'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Admin JSON data error: {str(e)}")
        return jsonify({'error': f'Failed to get JSON data: {str(e)}'}), 500

# ============= Course Endpoints =============

@app.route('/api/courses', methods=['GET'])
@login_required
def get_courses():
    """Get all courses (admin) or assigned courses (student)"""
    conn = get_connection()

    if session.get('role') == 'admin':
        # Admin sees all courses
        courses = conn.execute('''
            SELECT c.id, c.title, c.description, c.content_richtext, c.lyrics, c.audio, c.created_at
            FROM courses c
            ORDER BY c.created_at DESC
        ''').fetchall()
    else:
        # Students see only assigned courses
        courses = conn.execute('''
            SELECT c.id, c.title, c.description, c.content_richtext, c.lyrics, c.audio, c.created_at
            FROM courses c
            JOIN assigned_courses ac ON c.id = ac.course_id
            WHERE ac.user_id = ?
            ORDER BY c.created_at DESC
        ''', [session['user_id']]).fetchall()

    result = []
    for course in courses:
        # Get files for this course
        files = conn.execute('''
            SELECT id, filename, file_path
            FROM files
            WHERE course_id = ?
        ''', [course[0]]).fetchall()

        result.append({
            'id': course[0],
            'title': course[1],
            'description': course[2],
            'content_richtext': course[3],
            'lyrics': course[4],
            'audio': course[5],
            'created_at': str(course[6]),
            'files': [{'id': f[0], 'filename': f[1], 'file_path': f[2]} for f in files]
        })

    conn.close()
    return jsonify({'courses': result})

@app.route('/api/courses/<int:course_id>', methods=['GET'])
@login_required
def get_course(course_id):
    """Get a single course with files"""
    conn = get_connection()

    # Check if student has access to this course
    if session.get('role') == 'student':
        access = conn.execute('''
            SELECT COUNT(*) FROM assigned_courses
            WHERE user_id = ? AND course_id = ?
        ''', [session['user_id'], course_id]).fetchone()

        if access[0] == 0:
            conn.close()
            return jsonify({'error': 'Access denied'}), 403

    course = conn.execute('''
        SELECT id, title, description, content_richtext, lyrics, audio, created_at
        FROM courses
        WHERE id = ?
    ''', [course_id]).fetchone()

    if not course:
        conn.close()
        return jsonify({'error': 'Course not found'}), 404

    files = conn.execute('''
        SELECT id, filename, file_path
        FROM files
        WHERE course_id = ?
    ''', [course_id]).fetchall()

    result = {
        'id': course[0],
        'title': course[1],
        'description': course[2],
        'content_richtext': course[3],
        'lyrics': course[4],
        'audio': course[5],
        'created_at': str(course[6]),
        'files': [{'id': f[0], 'filename': f[1], 'file_path': f[2]} for f in files]
    }

    conn.close()
    return jsonify({'course': result})

@app.route('/api/courses', methods=['POST'])
@admin_required
def create_course():
    """Create a new course (admin only)"""
    data = request.json
    title = data.get('title')
    description = data.get('description', '')
    content_richtext = data.get('content_richtext', '')
    lyrics = data.get('lyrics', '')
    audio = data.get('audio', '')

    logger.info(f"Creating new course | Title: {title}")
    logger.info(f"Course creation data: title='{title}', description='{description}', content_richtext='{content_richtext[:100] if content_richtext else None}', lyrics='{lyrics[:100] if lyrics else None}', audio='{audio[:100] if audio else None}'")

    if not title:
        logger.warning(f"Course creation failed: Title required")
        return jsonify({'error': 'Title is required'}), 400

    conn = get_connection()
    log_database_operation('INSERT', 'courses', f'Title: {title}')
    
    # Check if we're using PostgreSQL or DuckDB for proper ID handling
    from backend.database_unified import use_postgres
    if use_postgres():
        conn.execute('''
            INSERT INTO courses (id, title, description, content_richtext, lyrics, audio)
            VALUES (nextval('courses_id_seq'), ?, ?, ?, ?, ?)
        ''', [title, description, content_richtext, lyrics, audio])
        course_id = conn.execute('SELECT MAX(id) FROM courses').fetchone()[0]
    else:
        # DuckDB - calculate next ID manually
        max_id_result = conn.execute('SELECT COALESCE(MAX(id), 0) FROM courses').fetchone()
        next_id = (max_id_result[0] if max_id_result else 0) + 1
        
        conn.execute('''
            INSERT INTO courses (id, title, description, content_richtext, lyrics, audio)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [next_id, title, description, content_richtext, lyrics, audio])
        course_id = next_id
    
    conn.commit()
    conn.close()

    # Backup to JSON after successful database operation
    try:
        sync_course_to_json(course_id)
        logger.info(f"Course {course_id} synced to JSON backup")
    except Exception as e:
        logger.warning(f"JSON backup failed for course {course_id}: {str(e)}")

    log_course_operation('CREATE', course_id, title)
    logger.info(f"✓ Course created successfully | ID: {course_id} | Title: {title}")

    return jsonify({'message': 'Course created', 'course_id': course_id}), 201

@app.route('/api/courses/<int:course_id>', methods=['PUT'])
@admin_required
def update_course(course_id):
    """Update a course (admin only)"""
    data = request.json
    title = data.get('title')
    description = data.get('description')
    content_richtext = data.get('content_richtext')
    lyrics = data.get('lyrics')
    audio = data.get('audio')

    logger.info(f"Updating course | ID: {course_id} | New title: {title}")
    logger.info(f"Course update data: title='{title}', description='{description}', content_richtext='{content_richtext[:100] if content_richtext else None}', lyrics='{lyrics[:100] if lyrics else None}', audio='{audio[:100] if audio else None}'")

    conn = get_connection()

    # Check if course exists
    log_database_operation('SELECT', 'courses', f'Check course exists: {course_id}')
    course = conn.execute('SELECT id FROM courses WHERE id = ?', [course_id]).fetchone()
    if not course:
        conn.close()
        logger.warning(f"✗ Course update failed: Course not found | ID: {course_id}")
        return jsonify({'error': 'Course not found'}), 404

    log_database_operation('UPDATE', 'courses', f'Course ID: {course_id}')
    logger.info(f"Executing UPDATE with title='{title}', description='{description}', content_richtext length={len(content_richtext or '')}, lyrics length={len(lyrics or '')}, audio length={len(audio or '')}")
    
    try:
        # Execute the update
        result = conn.execute('''
            UPDATE courses
            SET title = ?, description = ?, content_richtext = ?, lyrics = ?, audio = ?
            WHERE id = ?
        ''', [title, description, content_richtext, lyrics, audio, course_id])
        
        # Log number of rows affected
        rows_affected = result.rowcount if hasattr(result, 'rowcount') else "unknown"
        logger.info(f"Database UPDATE executed | Rows affected: {rows_affected}")
        
        # Commit the transaction
        conn.commit()
        logger.info(f"Database COMMIT executed")
        
        # Verify the update by reading back the data
        verify_result = conn.execute('SELECT title, description, content_richtext, lyrics, audio FROM courses WHERE id = ?', [course_id]).fetchone()
        if verify_result:
            logger.info(f"Verification: title='{verify_result[0]}', description='{verify_result[1]}', content_richtext length={len(verify_result[2] or '')}, lyrics length={len(verify_result[3] or '')}, audio length={len(verify_result[4] or '')}")
        else:
            logger.error(f"Verification failed: Course {course_id} not found after update")
        
        conn.close()
        logger.info(f"Database connection closed")
        
    except Exception as e:
        logger.error(f"Database update failed: {str(e)}")
        conn.rollback()
        conn.close()
        return jsonify({'error': 'Failed to update course'}), 500

    # Backup to JSON after successful database operation
    try:
        sync_course_to_json(course_id)
        logger.info(f"Course {course_id} synced to JSON backup")
    except Exception as e:
        logger.warning(f"JSON backup failed for course {course_id}: {str(e)}")

    log_course_operation('UPDATE', course_id, title)
    logger.info(f"✓ Course updated successfully | ID: {course_id} | Title: {title}")
    logger.info(f"✓ Course updated successfully | ID: {course_id} | Title: {title}")

    return jsonify({'message': 'Course updated'})

@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
@admin_required
def delete_course(course_id):
    """Delete a course (admin only)"""
    logger.info(f"Deleting course | ID: {course_id}")

    try:
        conn = get_connection()

        # First, check if course exists
        course = conn.execute('SELECT title FROM courses WHERE id = ?', [course_id]).fetchone()
        if not course:
            conn.close()
            logger.warning(f"✗ Course not found | ID: {course_id}")
            return jsonify({'error': 'Course not found'}), 404

        # Delete course files from filesystem
        log_database_operation('SELECT', 'files', f'Get files for course: {course_id}')
        files = conn.execute('SELECT id, file_path FROM files WHERE course_id = ?', [course_id]).fetchall()
        for file in files:
            try:
                if os.path.exists(file[1]):
                    os.remove(file[1])
                    log_file_operation('DELETE', file[1], f'Course deletion cleanup')
                    logger.debug(f"Deleted file: {file[1]}")
            except Exception as e:
                logger.warning(f"Failed to delete file: {file[1]} | Error: {str(e)}")

        # Delete related records first (in correct order to avoid foreign key constraints)
        
        # 1. Delete files from database
        log_database_operation('DELETE', 'files', f'All files for course: {course_id}')
        conn.execute('DELETE FROM files WHERE course_id = ?', [course_id])
        
        # 2. Delete course assignments
        log_database_operation('DELETE', 'assigned_courses', f'All assignments for course: {course_id}')
        conn.execute('DELETE FROM assigned_courses WHERE course_id = ?', [course_id])
        
        # 3. Finally delete the course
        log_database_operation('DELETE', 'courses', f'Course ID: {course_id}')
        conn.execute('DELETE FROM courses WHERE id = ?', [course_id])
        
        conn.commit()
        conn.close()

        # Backup to JSON after successful database operation
        try:
            sync_course_to_json(course_id)
            logger.info(f"Course deletion synced to JSON backup")
        except Exception as e:
            logger.warning(f"JSON backup failed after course deletion: {str(e)}")

        log_course_operation('DELETE', course_id)
        logger.info(f"✓ Course deleted successfully | ID: {course_id} | Title: {course[0]}")

        return jsonify({'message': 'Course deleted successfully'})
        
    except Exception as e:
        logger.error(f"✗ Failed to delete course | ID: {course_id} | Error: {str(e)}")
        return jsonify({'error': f'Failed to delete course: {str(e)}'}), 500

# ============= Assignment Endpoints =============

@app.route('/api/students', methods=['GET'])
@admin_required
def get_students():
    """Get all students (admin only)"""
    conn = get_connection()
    students = conn.execute('''
        SELECT id, email
        FROM users
        WHERE role = 'student'
        ORDER BY email
    ''').fetchall()
    conn.close()

    return jsonify({'students': [{'id': s[0], 'email': s[1]} for s in students]})

@app.route('/api/courses/<int:course_id>/assignments', methods=['GET'])
@admin_required
def get_course_assignments(course_id):
    """Get students assigned to a course (admin only)"""
    conn = get_connection()
    assignments = conn.execute('''
        SELECT u.id, u.email
        FROM users u
        JOIN assigned_courses ac ON u.id = ac.user_id
        WHERE ac.course_id = ?
    ''', [course_id]).fetchall()
    conn.close()

    return jsonify({'students': [{'id': s[0], 'email': s[1]} for s in assignments]})

@app.route('/api/courses/<int:course_id>/assign', methods=['POST'])
@admin_required
def assign_course(course_id):
    """Assign a course to students (admin only)"""
    data = request.json
    student_ids = data.get('student_ids', [])

    logger.info(f"Assigning course | Course ID: {course_id} | Students: {len(student_ids)}")

    conn = get_connection()

    # First, remove all existing assignments for this course
    log_database_operation('DELETE', 'assigned_courses', f'Clear existing assignments for course: {course_id}')
    conn.execute('DELETE FROM assigned_courses WHERE course_id = ?', [course_id])

    # If no students selected, just clear assignments and return
    if not student_ids:
        conn.commit()
        conn.close()
        logger.info(f"✓ All assignments cleared | Course ID: {course_id}")
        return jsonify({'message': 'All assignments cleared'})

    # Add new assignments
    assigned_count = 0
    for student_id in student_ids:
        try:
            log_database_operation('INSERT', 'assigned_courses', f'Student: {student_id}, Course: {course_id}')
            
            # Check if we're using PostgreSQL or DuckDB for proper ID handling
            from backend.database_unified import use_postgres
            if use_postgres():
                conn.execute('''
                    INSERT INTO assigned_courses (id, user_id, course_id)
                    VALUES (nextval('assigned_courses_id_seq'), ?, ?)
                ''', [student_id, course_id])
            else:
                # DuckDB - calculate next ID manually
                max_id_result = conn.execute('SELECT COALESCE(MAX(id), 0) FROM assigned_courses').fetchone()
                next_id = (max_id_result[0] if max_id_result else 0) + 1
                
                conn.execute('''
                    INSERT INTO assigned_courses (id, user_id, course_id)
                    VALUES (?, ?, ?)
                ''', [next_id, student_id, course_id])
            
            assigned_count += 1
        except Exception as e:
            logger.debug(f"Skip assignment (may already exist): Student {student_id} to Course {course_id}")

    conn.commit()
    conn.close()

    # Backup assignments to JSON after successful database operation
    try:
        backup_assignments_to_json()
        logger.info(f"Assignments synced to JSON backup")
    except Exception as e:
        logger.warning(f"JSON backup failed for assignments: {str(e)}")

    log_assignment_operation(course_id, student_ids, 'assign')
    logger.info(f"✓ Course assigned successfully | Course ID: {course_id} | Assigned: {assigned_count} students")

    return jsonify({'message': 'Course assigned successfully'})

# ============= File Upload Endpoints =============

@app.route('/api/courses/<int:course_id>/upload', methods=['POST'])
@admin_required
def upload_file(course_id):
    """Upload a file for a course (admin only)"""
    logger.info(f"File upload request for course ID: {course_id}")

    if 'file' not in request.files:
        logger.warning(f"File upload failed: No file provided | Course ID: {course_id}")
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning(f"File upload failed: Empty filename | Course ID: {course_id}")
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid filename conflicts
        import time
        filename = f"{int(time.time())}_{filename}"
        filepath = os.path.join(config.UPLOAD_FOLDER, filename)

        # Save file
        file.save(filepath)
        file_size = os.path.getsize(filepath)
        log_file_operation('UPLOAD', file.filename, f'Course ID: {course_id}, Size: {file_size} bytes')

        # Save file info to database
        conn = get_connection()
        log_database_operation('INSERT', 'files', f'File: {file.filename}, Course: {course_id}')
        
        # Check if we're using PostgreSQL or DuckDB for proper ID handling
        from backend.database_unified import use_postgres
        if use_postgres():
            conn.execute('''
                INSERT INTO files (id, course_id, filename, file_path)
                VALUES (nextval('files_id_seq'), ?, ?, ?)
            ''', [course_id, file.filename, filepath])
        else:
            # DuckDB - calculate next ID manually
            max_id_result = conn.execute('SELECT COALESCE(MAX(id), 0) FROM files').fetchone()
            next_id = (max_id_result[0] if max_id_result else 0) + 1
            
            conn.execute('''
                INSERT INTO files (id, course_id, filename, file_path)
                VALUES (?, ?, ?, ?)
            ''', [next_id, course_id, file.filename, filepath])
        
        conn.commit()

        file_id = conn.execute('SELECT MAX(id) FROM files').fetchone()[0]
        conn.close()

        logger.info(f"✓ File uploaded successfully | File: {file.filename} | Course ID: {course_id} | Size: {file_size} bytes")

        return jsonify({
            'message': 'File uploaded',
            'file': {
                'id': file_id,
                'filename': file.filename,
                'file_path': filepath
            }
        }), 201
    else:
        logger.warning(f"✗ File upload failed: File type not allowed | File: {file.filename} | Course ID: {course_id}")
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@admin_required
def delete_file(file_id):
    """Delete a file (admin only)"""
    logger.info(f"File deletion request | File ID: {file_id}")

    conn = get_connection()
    log_database_operation('SELECT', 'files', f'Get file path for ID: {file_id}')
    file = conn.execute('SELECT file_path FROM files WHERE id = ?', [file_id]).fetchone()

    if not file:
        conn.close()
        logger.warning(f"✗ File deletion failed: File not found | File ID: {file_id}")
        return jsonify({'error': 'File not found'}), 404

    file_path = file[0]

    # Delete from filesystem
    try:
        os.remove(file_path)
        log_file_operation('DELETE', file_path, f'File ID: {file_id}')
        logger.debug(f"File deleted from filesystem: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to delete file from filesystem: {file_path} | Error: {str(e)}")

    # Delete from database
    log_database_operation('DELETE', 'files', f'File ID: {file_id}')
    conn.execute('DELETE FROM files WHERE id = ?', [file_id])
    conn.commit()
    conn.close()

    logger.info(f"✓ File deleted successfully | File ID: {file_id} | Path: {file_path}")

    return jsonify({'message': 'File deleted'})

@app.route('/api/files/<int:file_id>/download', methods=['GET'])
@login_required
def download_file(file_id):
    """Download a file"""
    conn = get_connection()
    file = conn.execute('''
        SELECT f.file_path, f.filename, f.course_id
        FROM files f
        WHERE f.id = ?
    ''', [file_id]).fetchone()

    if not file:
        conn.close()
        return jsonify({'error': 'File not found'}), 404

    # Check if student has access to this course
    if session.get('role') == 'student':
        access = conn.execute('''
            SELECT COUNT(*) FROM assigned_courses
            WHERE user_id = ? AND course_id = ?
        ''', [session['user_id'], file[2]]).fetchone()

        if access[0] == 0:
            conn.close()
            return jsonify({'error': 'Access denied'}), 403

    conn.close()

    try:
        return send_file(file[0], as_attachment=True, download_name=file[1])
    except:
        return jsonify({'error': 'File not found on server'}), 404

# ============= Main Routes =============

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/admin-data')
def admin_data():
    return send_from_directory(app.static_folder, 'admin-data.html')

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    
    # Create initial JSON backup
    try:
        logger.info("Creating initial JSON backup...")
        backup_all_to_json()
    except Exception as e:
        logger.warning(f"Initial JSON backup failed: {str(e)}")
    
    app.run(debug=True, port=8000)
