from flask import Flask, request, jsonify, session, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import time
import json
from backend.database import get_connection, init_database, use_postgres, execute_query
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
            from backend.database import ensure_tables_exist
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
            from backend.database import ensure_tables_exist
            ensure_tables_exist()
            logger.info("Database tables verified for signup")
        except Exception as db_error:
            logger.error(f"Database initialization failed during signup: {str(db_error)}")
            return jsonify({'error': 'Service temporarily unavailable'}), 503

        # Check if email already exists
        log_database_operation('SELECT', 'users', f'Check existing email: {email}')
        existing = execute_query('SELECT id FROM users WHERE email = %s', [email], fetch_one=True)
        if existing:
            log_authentication('SIGNUP', email, False, 'Email already registered')
            logger.warning(f"✗ Signup failed: Email already exists | Email: {email}")
            return jsonify({'error': 'Email already registered'}), 400

        # Create new student account
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        log_database_operation('INSERT', 'users', f'New student account: {email}')
        
        # PostgreSQL handles auto-increment IDs automatically
        execute_query('''
            INSERT INTO users (email, hashed_password, role)
            VALUES (%s, %s, 'student')
        ''', [email, hashed_password])
        
        # Get the new user ID
        user = execute_query('SELECT id FROM users WHERE email = %s', [email], fetch_one=True)
        user_id = user['id']

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
            db_user = execute_query(
                'SELECT id, email, role FROM users WHERE id = %s AND email = %s',
                [user_id, email],
                fetch_one=True
            )
            
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
            if db_user['role'].lower() != role:
                logger.warning(f"Role mismatch for user {email}: session={role}, db={db_user['role']}")
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
        result = execute_query('SELECT COUNT(*) FROM users', fetch_one=True)
        return jsonify({
            'db_working': True,
            'user_count': result['count'] if result else 0,
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
        from backend.database import use_postgres, use_persistent_duckdb
        
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
            user_count = execute_query('SELECT COUNT(*) as count FROM users', fetch_one=True)['count']
            course_count = execute_query('SELECT COUNT(*) as count FROM courses', fetch_one=True)['count']
            assignment_count = execute_query('SELECT COUNT(*) as count FROM assigned_courses', fetch_one=True)['count']
            file_count = execute_query('SELECT COUNT(*) as count FROM files', fetch_one=True)['count']
            
            # PostgreSQL database info
            db_type = "PostgreSQL (Vercel)"
            db_path = os.environ.get('DATABASE_URL', 'Not configured')[:50] + "..."
            db_exists = True  # Assume exists if connection works
            db_size = "Managed by Vercel"
            persistent = True
            
        else:
            user_count = execute_query('SELECT COUNT(*) as count FROM users', fetch_one=True)['count']
            course_count = execute_query('SELECT COUNT(*) as count FROM courses', fetch_one=True)['count']
            assignment_count = execute_query('SELECT COUNT(*) as count FROM assigned_courses', fetch_one=True)['count']
            file_count = execute_query('SELECT COUNT(*) as count FROM files', fetch_one=True)['count']
            
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
    """Database sync endpoint - PostgreSQL handles persistence automatically"""
    try:
        from backend.database import use_persistent_duckdb
        
        if not use_persistent_duckdb():
            return jsonify({
                'message': 'PostgreSQL database is automatically persistent',
                'note': 'No manual sync required with Vercel PostgreSQL',
                'current_storage': 'PostgreSQL (Vercel)'
            }), 200
        
        # This shouldn't happen with PostgreSQL-only, but keeping for safety
        return jsonify({
            'error': 'Manual sync not supported with PostgreSQL',
            'current_storage': 'PostgreSQL (Vercel)'
        }), 400
            
    except Exception as e:
        logger.error(f"Database sync check error: {str(e)}")
        return jsonify({
            'message': 'PostgreSQL database is automatically persistent',
            'note': 'Vercel PostgreSQL handles persistence automatically'
        }), 200

@app.route('/api/me', methods=['GET'])
@login_required
def get_me():
    user = get_current_user()
    return jsonify({'user': user})

# ============= JSON Backup Endpoints =============

# ============= Admin Data Viewer Endpoints =============

@app.route('/api/admin/data/users', methods=['GET'])
@admin_required
def get_all_users_admin():
    """Get all users for admin data viewer (admin only)"""
    try:
        users = execute_query('''
            SELECT id, email, role, created_at
            FROM users
            ORDER BY id
        ''', fetch_all=True)
        
        # Handle case where no users exist
        if not users:
            users = []
        
        result = []
        for user in users:
            result.append({
                'id': user['id'],
                'email': user['email'],
                'role': user['role'],
                'created_at': str(user['created_at']) if user['created_at'] else None
            })
        
        return jsonify({'users': result})
        
    except Exception as e:
        logger.error(f"Admin users data error: {str(e)}")
        return jsonify({'error': f'Failed to get users data: {str(e)}'}), 500

@app.route('/api/admin/data/assignments', methods=['GET'])
@admin_required
def get_all_assignments_admin():
    """Get all assignments for admin data viewer (admin only)"""
    try:
        assignments = execute_query('''
            SELECT ac.id, ac.user_id, ac.course_id, u.email, c.title
            FROM assigned_courses ac
            JOIN users u ON ac.user_id = u.id
            JOIN courses c ON ac.course_id = c.id
            ORDER BY ac.id
        ''', fetch_all=True)
        
        # Handle case where no assignments exist
        if not assignments:
            assignments = []
        
        result = []
        for assignment in assignments:
            result.append({
                'id': assignment['id'],
                'user_id': assignment['user_id'],
                'course_id': assignment['course_id'],
                'user_email': assignment['email'],
                'course_title': assignment['title']
            })
        
        return jsonify({'assignments': result})
        
    except Exception as e:
        logger.error(f"Admin assignments data error: {str(e)}")
        return jsonify({'error': f'Failed to get assignments data: {str(e)}'}), 500

@app.route('/api/admin/data/files', methods=['GET'])
@admin_required
def get_all_files_admin():
    """Get all files for admin data viewer (admin only)"""
    try:
        files = execute_query('''
            SELECT f.id, f.course_id, f.filename, f.file_path, c.title
            FROM files f
            JOIN courses c ON f.course_id = c.id
            ORDER BY f.id
        ''', fetch_all=True)
        
        # Handle case where no files exist
        if not files:
            files = []
        
        result = []
        for file in files:
            # Check if file exists and get size
            file_exists = os.path.exists(file['file_path']) if file['file_path'] else False
            file_size = os.path.getsize(file['file_path']) if file_exists else 0
            
            result.append({
                'id': file['id'],
                'course_id': file['course_id'],
                'filename': file['filename'],
                'file_path': file['file_path'],
                'course_title': file['title'],
                'file_exists': file_exists,
                'file_size_bytes': file_size
            })
        
        return jsonify({'files': result})
        
    except Exception as e:
        logger.error(f"Admin files data error: {str(e)}")
        return jsonify({'error': f'Failed to get files data: {str(e)}'}), 500

# ============= Course Endpoints =============

@app.route('/api/courses', methods=['GET'])
@login_required
def get_courses():
    """Get all courses (admin) or assigned courses (student)"""
    
    if session.get('role') == 'admin':
        # Admin sees all courses
        courses = execute_query('''
            SELECT c.id, c.title, c.description, c.content_richtext, c.lyrics, c.audio, c.created_at
            FROM courses c
            ORDER BY c.created_at DESC
        ''', fetch_all=True)
    else:
        # Students see only assigned courses
        courses = execute_query('''
            SELECT c.id, c.title, c.description, c.content_richtext, c.lyrics, c.audio, c.created_at
            FROM courses c
            JOIN assigned_courses ac ON c.id = ac.course_id
            WHERE ac.user_id = %s
            ORDER BY c.created_at DESC
        ''', [session['user_id']], fetch_all=True)

    # Get file count for each course
    course_list = []
    for course in courses or []:
        files = execute_query('''
            SELECT COUNT(*) as count FROM files WHERE course_id = %s
        ''', [course['id']], fetch_one=True)

        course_list.append({
            'id': course['id'],
            'title': course['title'],
            'description': course['description'],
            'content_richtext': course['content_richtext'],
            'lyrics': course['lyrics'],
            'audio': course['audio'],
            'created_at': str(course['created_at']),
            'file_count': files['count'] if files else 0
        })

    return jsonify(course_list)

@app.route('/api/courses/<int:course_id>', methods=['GET'])
@login_required
def get_course(course_id):
    """Get a single course with files"""
    
    # Check if student has access to this course
    if session.get('role') == 'student':
        access = execute_query('''
            SELECT COUNT(*) as count FROM assigned_courses
            WHERE user_id = %s AND course_id = %s
        ''', [session['user_id'], course_id], fetch_one=True)

        if access['count'] == 0:
            return jsonify({'error': 'Access denied'}), 403

    course = execute_query('''
        SELECT id, title, description, content_richtext, lyrics, audio, created_at
        FROM courses
        WHERE id = %s
    ''', [course_id], fetch_one=True)

    if not course:
        return jsonify({'error': 'Course not found'}), 404

    files = execute_query('''
        SELECT id, filename, file_path
        FROM files
        WHERE course_id = %s
    ''', [course_id], fetch_all=True)

    # Handle case where no files exist
    if not files:
        files = []

    result = {
        'id': course['id'],
        'title': course['title'],
        'description': course['description'],
        'content_richtext': course['content_richtext'],
        'lyrics': course['lyrics'],
        'audio': course['audio'],
        'created_at': str(course['created_at']),
        'files': [{'id': f['id'], 'filename': f['filename'], 'file_path': f['file_path']} for f in files]
    }

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

    log_database_operation('INSERT', 'courses', f'Title: {title}')
    
    # PostgreSQL handles auto-increment IDs automatically
    execute_query('''
        INSERT INTO courses (title, description, content_richtext, lyrics, audio)
        VALUES (%s, %s, %s, %s, %s)
    ''', [title, description, content_richtext, lyrics, audio])
    
    # Get the newly created course ID
    course_result = execute_query('SELECT id FROM courses WHERE title = %s ORDER BY id DESC LIMIT 1', [title], fetch_one=True)
    course_id = course_result['id'] if course_result else None

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

    # Check if course exists
    log_database_operation('SELECT', 'courses', f'Check course exists: {course_id}')
    course = execute_query('SELECT id FROM courses WHERE id = %s', [course_id], fetch_one=True)
    if not course:
        logger.warning(f"✗ Course update failed: Course not found | ID: {course_id}")
        return jsonify({'error': 'Course not found'}), 404

    log_database_operation('UPDATE', 'courses', f'Course ID: {course_id}')
    logger.info(f"Executing UPDATE with title='{title}', description='{description}', content_richtext length={len(content_richtext or '')}, lyrics length={len(lyrics or '')}, audio length={len(audio or '')}")
    
    try:
        # Execute the update
        execute_query('''
            UPDATE courses
            SET title = %s, description = %s, content_richtext = %s, lyrics = %s, audio = %s
            WHERE id = %s
        ''', [title, description, content_richtext, lyrics, audio, course_id])
        
        logger.info(f"Database UPDATE executed successfully")
        
        # Verify the update by reading back the data
        verify_result = execute_query('SELECT title, description, content_richtext, lyrics, audio FROM courses WHERE id = %s', [course_id], fetch_one=True)
        if verify_result:
            logger.info(f"Verification: title='{verify_result['title']}', description='{verify_result['description']}', content_richtext length={len(verify_result['content_richtext'] or '')}, lyrics length={len(verify_result['lyrics'] or '')}, audio length={len(verify_result['audio'] or '')}")
        else:
            logger.error(f"Verification failed: Course {course_id} not found after update")
        
    except Exception as e:
        logger.error(f"Database update failed: {str(e)}")
        return jsonify({'error': 'Failed to update course'}), 500

    log_course_operation('UPDATE', course_id, title)
    logger.info(f"✓ Course updated successfully | ID: {course_id} | Title: {title}")

    return jsonify({'message': 'Course updated'})

@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
@admin_required
def delete_course(course_id):
    """Delete a course (admin only)"""
    logger.info(f"Deleting course | ID: {course_id}")

    try:
        # First, check if course exists
        course = execute_query('SELECT title FROM courses WHERE id = %s', [course_id], fetch_one=True)
        if not course:
            logger.warning(f"✗ Course not found | ID: {course_id}")
            return jsonify({'error': 'Course not found'}), 404

        # Delete course files from filesystem
        log_database_operation('SELECT', 'files', f'Get files for course: {course_id}')
        files = execute_query('SELECT id, file_path FROM files WHERE course_id = %s', [course_id], fetch_all=True)
        for file in files or []:
            try:
                if os.path.exists(file['file_path']):
                    os.remove(file['file_path'])
                    log_file_operation('DELETE', file['file_path'], f'Course deletion cleanup')
                    logger.debug(f"Deleted file: {file['file_path']}")
            except Exception as e:
                logger.warning(f"Failed to delete file: {file['file_path']} | Error: {str(e)}")

        # Delete related records first (in correct order to avoid foreign key constraints)
        
        # 1. Delete files from database
        log_database_operation('DELETE', 'files', f'All files for course: {course_id}')
        execute_query('DELETE FROM files WHERE course_id = %s', [course_id])
        
        # 2. Delete course assignments
        log_database_operation('DELETE', 'assigned_courses', f'All assignments for course: {course_id}')
        execute_query('DELETE FROM assigned_courses WHERE course_id = %s', [course_id])
        
        # 3. Finally delete the course
        log_database_operation('DELETE', 'courses', f'Course ID: {course_id}')
        execute_query('DELETE FROM courses WHERE id = %s', [course_id])

        log_course_operation('DELETE', course_id)
        logger.info(f"✓ Course deleted successfully | ID: {course_id} | Title: {course['title']}")

        return jsonify({'message': 'Course deleted successfully'})
        
    except Exception as e:
        logger.error(f"✗ Failed to delete course | ID: {course_id} | Error: {str(e)}")
        return jsonify({'error': f'Failed to delete course: {str(e)}'}), 500

# ============= Assignment Endpoints =============

@app.route('/api/students', methods=['GET'])
@admin_required
def get_students():
    """Get all students (admin only)"""
    students = execute_query('''
        SELECT id, email
        FROM users
        WHERE role = 'student'
        ORDER BY email
    ''', fetch_all=True)

    # Handle case where no students exist
    if not students:
        students = []

    return jsonify({'students': [{'id': s['id'], 'email': s['email']} for s in students]})

@app.route('/api/courses/<int:course_id>/assignments', methods=['GET'])
@admin_required
def get_course_assignments(course_id):
    """Get students assigned to a course (admin only)"""
    assignments = execute_query('''
        SELECT u.id, u.email
        FROM users u
        JOIN assigned_courses ac ON u.id = ac.user_id
        WHERE ac.course_id = %s
    ''', [course_id], fetch_all=True)

    # Handle case where no assignments exist
    if not assignments:
        assignments = []

    return jsonify({'students': [{'id': s['id'], 'email': s['email']} for s in assignments]})

@app.route('/api/courses/<int:course_id>/assign', methods=['POST'])
@admin_required
def assign_course(course_id):
    """Assign a course to students (admin only)"""
    data = request.json
    student_ids = data.get('student_ids', [])

    logger.info(f"Assigning course | Course ID: {course_id} | Students: {len(student_ids)}")

    # First, remove all existing assignments for this course
    log_database_operation('DELETE', 'assigned_courses', f'Clear existing assignments for course: {course_id}')
    execute_query('DELETE FROM assigned_courses WHERE course_id = %s', [course_id])

    # If no students selected, just clear assignments and return
    if not student_ids:
        logger.info(f"✓ All assignments cleared | Course ID: {course_id}")
        return jsonify({'message': 'All assignments cleared'})

    # Add new assignments
    assigned_count = 0
    for student_id in student_ids:
        try:
            log_database_operation('INSERT', 'assigned_courses', f'Student: {student_id}, Course: {course_id}')
            
            # PostgreSQL uses sequences for auto-increment IDs
            execute_query('''
                INSERT INTO assigned_courses (user_id, course_id)
                VALUES (%s, %s)
            ''', [student_id, course_id])
            
            assigned_count += 1
        except Exception as e:
            logger.debug(f"Skip assignment (may already exist): Student {student_id} to Course {course_id}")

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
        log_database_operation('INSERT', 'files', f'File: {file.filename}, Course: {course_id}')
        
        # PostgreSQL uses sequences for auto-increment IDs
        execute_query('''
            INSERT INTO files (course_id, filename, file_path)
            VALUES (%s, %s, %s)
        ''', [course_id, file.filename, filepath])
        
        # Get the inserted file ID
        file_result = execute_query('SELECT MAX(id) as id FROM files', fetch_one=True)
        file_id = file_result['id']

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

    log_database_operation('SELECT', 'files', f'Get file path for ID: {file_id}')
    file = execute_query('SELECT file_path FROM files WHERE id = %s', [file_id], fetch_one=True)

    if not file:
        logger.warning(f"✗ File deletion failed: File not found | File ID: {file_id}")
        return jsonify({'error': 'File not found'}), 404

    file_path = file['file_path']

    # Delete from filesystem
    try:
        os.remove(file_path)
        log_file_operation('DELETE', file_path, f'File ID: {file_id}')
        logger.debug(f"File deleted from filesystem: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to delete file from filesystem: {file_path} | Error: {str(e)}")

    # Delete from database
    log_database_operation('DELETE', 'files', f'File ID: {file_id}')
    execute_query('DELETE FROM files WHERE id = %s', [file_id])

    logger.info(f"✓ File deleted successfully | File ID: {file_id} | Path: {file_path}")

    return jsonify({'message': 'File deleted'})

@app.route('/api/files/<int:file_id>/download', methods=['GET'])
@login_required
def download_file(file_id):
    """Download a file"""
    file = execute_query('''
        SELECT f.file_path, f.filename, f.course_id
        FROM files f
        WHERE f.id = %s
    ''', [file_id], fetch_one=True)

    if not file:
        return jsonify({'error': 'File not found'}), 404

    # Check if student has access to this course
    if session.get('role') == 'student':
        access = execute_query('''
            SELECT COUNT(*) as count FROM assigned_courses
            WHERE user_id = %s AND course_id = %s
        ''', [session['user_id'], file['course_id']], fetch_one=True)

        if access['count'] == 0:
            return jsonify({'error': 'Access denied'}), 403

    try:
        return send_file(file['file_path'], as_attachment=True, download_name=file['filename'])
    except:
        return jsonify({'error': 'File not found on server'}), 404

# ============= Main Routes =============

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/admin-data')
def admin_data():
    return send_from_directory(app.static_folder, 'admin-data.html')

@app.route('/admin-users')
def admin_users():
    return send_from_directory(app.static_folder, 'admin-users.html')

@app.route('/admin-environment')
def admin_environment():
    return send_from_directory(app.static_folder, 'admin-environment.html')

@app.route('/api/admin/users/credentials', methods=['GET'])
@admin_required
def get_user_credentials_admin():
    """Get all user credentials including hashed passwords (admin only - for debugging)"""
    try:
        users = execute_query('''
            SELECT id, email, hashed_password, role, created_at
            FROM users
            ORDER BY id
        ''', fetch_all=True)
        
        # Handle case where no users exist
        if not users:
            users = []
            
        result = []
        for user in users:
            result.append({
                'id': user['id'],
                'email': user['email'],
                'hashed_password': user['hashed_password'],  # Include hashed password for admin view
                'role': user['role'],
                'created_at': str(user['created_at']) if user['created_at'] else None
            })
        return jsonify({'users': result})
        
    except Exception as e:
        logger.error(f"Admin user credentials error: {str(e)}")
        return jsonify({'error': f'Failed to get user credentials: {str(e)}'}), 500

@app.route('/api/admin/environment', methods=['GET'])
@admin_required
def get_environment_variables():
    """Get all required environment variables and their status (admin only)"""
    try:
        # Define all environment variables used by the application
        env_vars = {
            'core': {
                'SECRET_KEY': {
                    'description': 'Flask secret key for session encryption',
                    'required': True,
                    'default': 'dev-secret-key-change-in-production',
                    'category': 'Security'
                },
                'FLASK_ENV': {
                    'description': 'Flask environment (development/production)',
                    'required': False,
                    'default': 'development',
                    'category': 'Application'
                },
                'VERCEL': {
                    'description': 'Vercel deployment flag (automatically set)',
                    'required': False,
                    'default': None,
                    'category': 'Deployment'
                }
            },
            'database': {
                'DATABASE_URL': {
                    'description': 'PostgreSQL connection string',
                    'required': False,
                    'default': None,
                    'category': 'Database'
                },
                'DB_HOST': {
                    'description': 'PostgreSQL host address',
                    'required': False,
                    'default': None,
                    'category': 'Database'
                },
                'DB_PORT': {
                    'description': 'PostgreSQL port',
                    'required': False,
                    'default': '5432',
                    'category': 'Database'
                },
                'DB_NAME': {
                    'description': 'PostgreSQL database name',
                    'required': False,
                    'default': None,
                    'category': 'Database'
                },
                'DB_USER': {
                    'description': 'PostgreSQL username',
                    'required': False,
                    'default': None,
                    'category': 'Database'
                },
                'DB_PASSWORD': {
                    'description': 'PostgreSQL password',
                    'required': False,
                    'default': None,
                    'category': 'Database'
                },
                'DB_PATH': {
                    'description': 'DuckDB file path',
                    'required': False,
                    'default': 'student_courses.db (local) / /tmp/student_courses.db (Vercel)',
                    'category': 'Database'
                }
            },
            'storage': {
                'UPLOAD_FOLDER': {
                    'description': 'File upload directory',
                    'required': False,
                    'default': 'uploads (local) / /tmp/uploads (Vercel)',
                    'category': 'Storage'
                },
                'MAX_CONTENT_LENGTH': {
                    'description': 'Maximum upload file size in bytes',
                    'required': False,
                    'default': '16777216 (16MB)',
                    'category': 'Storage'
                },
                'NETWORK_DB_PATH': {
                    'description': 'Network-mounted database path',
                    'required': False,
                    'default': None,
                    'category': 'Storage'
                },
                'VERCEL_VOLUME_PATH': {
                    'description': 'Vercel volume mount path',
                    'required': False,
                    'default': None,
                    'category': 'Storage'
                }
            },
            'cloud_storage': {
                'AWS_ACCESS_KEY_ID': {
                    'description': 'AWS access key for S3 storage',
                    'required': False,
                    'default': None,
                    'category': 'Cloud Storage'
                },
                'AWS_SECRET_ACCESS_KEY': {
                    'description': 'AWS secret key for S3 storage',
                    'required': False,
                    'default': None,
                    'category': 'Cloud Storage'
                },
                'S3_BUCKET': {
                    'description': 'S3 bucket name',
                    'required': False,
                    'default': 'student-course-db',
                    'category': 'Cloud Storage'
                },
                'S3_KEY': {
                    'description': 'S3 object key for database file',
                    'required': False,
                    'default': 'student_courses.db',
                    'category': 'Cloud Storage'
                },
                'GOOGLE_APPLICATION_CREDENTIALS': {
                    'description': 'Path to Google Cloud service account JSON',
                    'required': False,
                    'default': None,
                    'category': 'Cloud Storage'
                },
                'GCS_BUCKET': {
                    'description': 'Google Cloud Storage bucket name',
                    'required': False,
                    'default': 'student-course-db',
                    'category': 'Cloud Storage'
                },
                'GCS_BLOB': {
                    'description': 'Google Cloud Storage blob name',
                    'required': False,
                    'default': 'student_courses.db',
                    'category': 'Cloud Storage'
                },
                'BLOB_READ_WRITE_TOKEN': {
                    'description': 'Vercel Blob storage access token',
                    'required': False,
                    'default': None,
                    'category': 'Cloud Storage'
                },
                'BLOB_URL': {
                    'description': 'Vercel Blob storage URL',
                    'required': False,
                    'default': None,
                    'category': 'Cloud Storage'
                },
                'BLOB_NAME': {
                    'description': 'Vercel Blob storage file name',
                    'required': False,
                    'default': 'student_courses.db',
                    'category': 'Cloud Storage'
                }
            },
            'server': {
                'CORS_ORIGINS': {
                    'description': 'Comma-separated list of allowed CORS origins',
                    'required': False,
                    'default': '*',
                    'category': 'Server'
                },
                'AWS_LAMBDA_FUNCTION_NAME': {
                    'description': 'AWS Lambda function name (auto-detected)',
                    'required': False,
                    'default': None,
                    'category': 'Server'
                },
                'LAMBDA_RUNTIME_DIR': {
                    'description': 'AWS Lambda runtime directory (auto-detected)',
                    'required': False,
                    'default': None,
                    'category': 'Server'
                },
                'SERVERLESS': {
                    'description': 'Generic serverless environment flag',
                    'required': False,
                    'default': None,
                    'category': 'Server'
                }
            }
        }
        
        # Check current values and status
        result = {
            'environment_type': 'vercel' if os.environ.get('VERCEL') == '1' else 'local',
            'timestamp': time.time(),
            'categories': {}
        }
        
        for category, variables in env_vars.items():
            result['categories'][category] = {
                'variables': {},
                'configured_count': 0,
                'total_count': len(variables)
            }
            
            for var_name, var_info in variables.items():
                current_value = os.environ.get(var_name)
                is_set = current_value is not None
                is_using_default = not is_set and var_info.get('default') is not None
                
                # For sensitive variables, don't show actual values
                display_value = current_value
                if var_name in ['SECRET_KEY', 'DB_PASSWORD', 'AWS_SECRET_ACCESS_KEY', 'BLOB_READ_WRITE_TOKEN'] and current_value:
                    display_value = f"***{current_value[-4:]}" if len(current_value) > 4 else "***"
                
                result['categories'][category]['variables'][var_name] = {
                    'description': var_info['description'],
                    'required': var_info['required'],
                    'is_set': is_set,
                    'value': display_value,
                    'using_default': is_using_default,
                    'default_value': var_info['default'],
                    'category_name': var_info['category']
                }
                
                if is_set:
                    result['categories'][category]['configured_count'] += 1
        
        # Add deployment recommendations
        result['recommendations'] = []
        
        if result['environment_type'] == 'local':
            if not os.environ.get('SECRET_KEY'):
                result['recommendations'].append('Set SECRET_KEY for production security')
        else:  # Vercel
            if not os.environ.get('SECRET_KEY'):
                result['recommendations'].append('CRITICAL: Set SECRET_KEY in Vercel environment variables')
            if not os.environ.get('BLOB_READ_WRITE_TOKEN'):
                result['recommendations'].append('Consider setting BLOB_READ_WRITE_TOKEN for persistent storage')
        
        # Add summary statistics
        total_vars = sum(len(variables) for variables in env_vars.values())
        set_vars = sum(1 for category in result['categories'].values() for var in category['variables'].values() if var['is_set'])
        
        result['summary'] = {
            'total_variables': total_vars,
            'configured_variables': set_vars,
            'configuration_percentage': round((set_vars / total_vars) * 100, 1) if total_vars > 0 else 0
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Environment variables error: {str(e)}")
        return jsonify({'error': f'Failed to get environment variables: {str(e)}'}), 500

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    
    app.run(debug=True, port=8000)
