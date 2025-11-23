from flask import Flask, request, jsonify, session, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import time
from backend.database import get_connection, init_database
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

        user = verify_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['email'] = user['email']
            session['role'] = user['role']

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
        conn.execute('''
            INSERT INTO users (id, email, hashed_password, role)
            VALUES (nextval('users_id_seq'), ?, ?, 'student')
        ''', [email, hashed_password])
        conn.commit()

        # Get the new user ID
        user_id = conn.execute('SELECT MAX(id) FROM users').fetchone()[0]
        conn.close()

        # Auto-login after signup
        session['user_id'] = user_id
        session['email'] = email
        session['role'] = 'student'

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
    """Check if user is authenticated"""
    try:
        # First check if session exists and has user_id
        if not session or 'user_id' not in session:
            return jsonify({'authenticated': False})
        
        # Get session data safely
        user_id = session.get('user_id')
        email = session.get('email')
        role = session.get('role')
        
        # Validate session data - all fields must be present and valid
        if not user_id or not email or not role:
            # Clear corrupted session silently
            try:
                session.clear()
            except:
                pass
            return jsonify({'authenticated': False})
        
        # Validate user_id is a number
        if not isinstance(user_id, (int, str)) or (isinstance(user_id, str) and not user_id.isdigit()):
            try:
                session.clear()
            except:
                pass
            return jsonify({'authenticated': False})
        
        # Validate role is valid
        if role not in ['admin', 'student']:
            try:
                session.clear()
            except:
                pass
            return jsonify({'authenticated': False})
        
        # All validations passed - return authenticated user
        return jsonify({
            'authenticated': True,
            'user': {
                'id': int(user_id) if isinstance(user_id, str) else user_id,
                'email': str(email),
                'role': str(role)
            }
        })
    
    except Exception as e:
        # Log error without using the potentially problematic logger functions
        import traceback
        print(f"Check-auth error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Clear session safely and return unauthenticated
        try:
            session.clear()
        except:
            pass
        return jsonify({'authenticated': False})

@app.route('/api/me', methods=['GET'])
@login_required
def get_me():
    user = get_current_user()
    return jsonify({'user': user})

# ============= Course Endpoints =============

@app.route('/api/courses', methods=['GET'])
@login_required
def get_courses():
    """Get all courses (admin) or assigned courses (student)"""
    conn = get_connection()

    if session.get('role') == 'admin':
        # Admin sees all courses
        courses = conn.execute('''
            SELECT c.id, c.title, c.description, c.content_richtext, c.created_at
            FROM courses c
            ORDER BY c.created_at DESC
        ''').fetchall()
    else:
        # Students see only assigned courses
        courses = conn.execute('''
            SELECT c.id, c.title, c.description, c.content_richtext, c.created_at
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
            'created_at': str(course[4]),
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
        SELECT id, title, description, content_richtext, created_at
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
        'created_at': str(course[4]),
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

    logger.info(f"Creating new course | Title: {title}")

    if not title:
        logger.warning(f"Course creation failed: Title required")
        return jsonify({'error': 'Title is required'}), 400

    conn = get_connection()
    log_database_operation('INSERT', 'courses', f'Title: {title}')
    conn.execute('''
        INSERT INTO courses (id, title, description, content_richtext)
        VALUES (nextval('courses_id_seq'), ?, ?, ?)
    ''', [title, description, content_richtext])
    conn.commit()

    # Get the newly created course ID
    course_id = conn.execute('SELECT MAX(id) FROM courses').fetchone()[0]
    conn.close()

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

    logger.info(f"Updating course | ID: {course_id} | New title: {title}")

    conn = get_connection()

    # Check if course exists
    log_database_operation('SELECT', 'courses', f'Check course exists: {course_id}')
    course = conn.execute('SELECT id FROM courses WHERE id = ?', [course_id]).fetchone()
    if not course:
        conn.close()
        logger.warning(f"✗ Course update failed: Course not found | ID: {course_id}")
        return jsonify({'error': 'Course not found'}), 404

    log_database_operation('UPDATE', 'courses', f'Course ID: {course_id}')
    conn.execute('''
        UPDATE courses
        SET title = ?, description = ?, content_richtext = ?
        WHERE id = ?
    ''', [title, description, content_richtext, course_id])
    conn.commit()
    conn.close()

    log_course_operation('UPDATE', course_id, title)
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
            conn.execute('''
                INSERT INTO assigned_courses (id, user_id, course_id)
                VALUES (nextval('assigned_courses_id_seq'), ?, ?)
            ''', [student_id, course_id])
            assigned_count += 1
        except Exception as e:
            logger.debug(f"Skip assignment (may already exist): Student {student_id} to Course {course_id}")

    conn.commit()
    conn.close()

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
        conn.execute('''
            INSERT INTO files (id, course_id, filename, file_path)
            VALUES (nextval('files_id_seq'), ?, ?, ?)
        ''', [course_id, file.filename, filepath])
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

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    app.run(debug=True, port=8000)
