"""
JSON storage module for backing up course data alongside DuckDB
Provides JSON export/import functionality for data portability
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from backend.logger import logger
from backend.database_unified import get_connection

# JSON storage configuration
JSON_STORAGE_DIR = "json_backup"
COURSES_JSON_FILE = "courses.json"
USERS_JSON_FILE = "users.json"
ASSIGNMENTS_JSON_FILE = "assignments.json"
FILES_JSON_FILE = "files.json"

def ensure_json_directory():
    """Ensure the JSON storage directory exists"""
    Path(JSON_STORAGE_DIR).mkdir(exist_ok=True)

def get_json_file_path(filename):
    """Get full path for JSON file"""
    return os.path.join(JSON_STORAGE_DIR, filename)

def backup_courses_to_json():
    """Export all courses to JSON format"""
    try:
        ensure_json_directory()
        conn = get_connection()
        
        # Get all courses with their data
        courses = conn.execute('''
            SELECT id, title, description, content_richtext, lyrics, audio, created_at
            FROM courses
            ORDER BY id
        ''').fetchall()
        
        courses_data = []
        for course in courses:
            course_dict = {
                'id': course[0],
                'title': course[1],
                'description': course[2],
                'content_richtext': course[3],
                'lyrics': course[4],
                'audio': course[5],
                'created_at': str(course[6]),
                'backup_timestamp': datetime.now().isoformat()
            }
            courses_data.append(course_dict)
        
        # Write to JSON file
        json_path = get_json_file_path(COURSES_JSON_FILE)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'courses': courses_data,
                'total_count': len(courses_data),
                'last_backup': datetime.now().isoformat(),
                'backup_version': '1.0'
            }, f, indent=2, ensure_ascii=False)
        
        conn.close()
        logger.info(f"Courses backed up to JSON: {len(courses_data)} courses saved to {json_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to backup courses to JSON: {str(e)}")
        return False

def backup_users_to_json():
    """Export all users to JSON format (excluding passwords)"""
    try:
        ensure_json_directory()
        conn = get_connection()
        
        # Get all users (excluding password hashes for security)
        users = conn.execute('''
            SELECT id, email, role, created_at
            FROM users
            ORDER BY id
        ''').fetchall()
        
        users_data = []
        for user in users:
            user_dict = {
                'id': user[0],
                'email': user[1],
                'role': user[2],
                'created_at': str(user[3]) if user[3] else None,
                'backup_timestamp': datetime.now().isoformat()
            }
            users_data.append(user_dict)
        
        # Write to JSON file
        json_path = get_json_file_path(USERS_JSON_FILE)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'users': users_data,
                'total_count': len(users_data),
                'last_backup': datetime.now().isoformat(),
                'backup_version': '1.0',
                'note': 'Password hashes excluded for security'
            }, f, indent=2, ensure_ascii=False)
        
        conn.close()
        logger.info(f"Users backed up to JSON: {len(users_data)} users saved to {json_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to backup users to JSON: {str(e)}")
        return False

def backup_assignments_to_json():
    """Export all course assignments to JSON format"""
    try:
        ensure_json_directory()
        conn = get_connection()
        
        # Get all assignments with user and course details
        assignments = conn.execute('''
            SELECT ac.id, ac.user_id, ac.course_id, u.email, c.title
            FROM assigned_courses ac
            JOIN users u ON ac.user_id = u.id
            JOIN courses c ON ac.course_id = c.id
            ORDER BY ac.id
        ''').fetchall()
        
        assignments_data = []
        for assignment in assignments:
            assignment_dict = {
                'id': assignment[0],
                'user_id': assignment[1],
                'course_id': assignment[2],
                'user_email': assignment[3],
                'course_title': assignment[4],
                'backup_timestamp': datetime.now().isoformat()
            }
            assignments_data.append(assignment_dict)
        
        # Write to JSON file
        json_path = get_json_file_path(ASSIGNMENTS_JSON_FILE)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'assignments': assignments_data,
                'total_count': len(assignments_data),
                'last_backup': datetime.now().isoformat(),
                'backup_version': '1.0'
            }, f, indent=2, ensure_ascii=False)
        
        conn.close()
        logger.info(f"Assignments backed up to JSON: {len(assignments_data)} assignments saved to {json_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to backup assignments to JSON: {str(e)}")
        return False

def backup_files_to_json():
    """Export all file metadata to JSON format"""
    try:
        ensure_json_directory()
        conn = get_connection()
        
        # Get all files with course details
        files = conn.execute('''
            SELECT f.id, f.course_id, f.filename, f.file_path, c.title
            FROM files f
            JOIN courses c ON f.course_id = c.id
            ORDER BY f.id
        ''').fetchall()
        
        files_data = []
        for file in files:
            # Check if file exists on filesystem
            file_exists = os.path.exists(file[3]) if file[3] else False
            file_size = os.path.getsize(file[3]) if file_exists else 0
            
            file_dict = {
                'id': file[0],
                'course_id': file[1],
                'filename': file[2],
                'file_path': file[3],
                'course_title': file[4],
                'file_exists': file_exists,
                'file_size_bytes': file_size,
                'backup_timestamp': datetime.now().isoformat()
            }
            files_data.append(file_dict)
        
        # Write to JSON file
        json_path = get_json_file_path(FILES_JSON_FILE)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'files': files_data,
                'total_count': len(files_data),
                'last_backup': datetime.now().isoformat(),
                'backup_version': '1.0',
                'note': 'Contains file metadata only, not file contents'
            }, f, indent=2, ensure_ascii=False)
        
        conn.close()
        logger.info(f"Files backed up to JSON: {len(files_data)} files saved to {json_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to backup files to JSON: {str(e)}")
        return False

def backup_all_to_json():
    """Backup all data to JSON files"""
    try:
        logger.info("Starting full JSON backup...")
        
        results = {
            'courses': backup_courses_to_json(),
            'users': backup_users_to_json(),
            'assignments': backup_assignments_to_json(),
            'files': backup_files_to_json()
        }
        
        success_count = sum(results.values())
        total_count = len(results)
        
        logger.info(f"JSON backup completed: {success_count}/{total_count} successful")
        return success_count == total_count
        
    except Exception as e:
        logger.error(f"Failed to complete full JSON backup: {str(e)}")
        return False

def get_json_backup_status():
    """Get status of JSON backup files"""
    try:
        ensure_json_directory()
        status = {
            'backup_directory': JSON_STORAGE_DIR,
            'backup_directory_exists': os.path.exists(JSON_STORAGE_DIR),
            'files': {}
        }
        
        json_files = [COURSES_JSON_FILE, USERS_JSON_FILE, ASSIGNMENTS_JSON_FILE, FILES_JSON_FILE]
        
        for filename in json_files:
            file_path = get_json_file_path(filename)
            file_exists = os.path.exists(file_path)
            
            file_info = {
                'exists': file_exists,
                'path': file_path,
                'size_bytes': 0,
                'last_modified': None,
                'record_count': 0
            }
            
            if file_exists:
                try:
                    file_stat = os.stat(file_path)
                    file_info['size_bytes'] = file_stat.st_size
                    file_info['last_modified'] = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    
                    # Try to read record count
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        file_info['record_count'] = data.get('total_count', 0)
                        file_info['last_backup'] = data.get('last_backup')
                        
                except Exception as e:
                    file_info['error'] = str(e)
            
            status['files'][filename] = file_info
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get JSON backup status: {str(e)}")
        return {'error': str(e)}

def load_courses_from_json():
    """Load courses data from JSON (for reference/import)"""
    try:
        json_path = get_json_file_path(COURSES_JSON_FILE)
        if not os.path.exists(json_path):
            return None
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('courses', [])
            
    except Exception as e:
        logger.error(f"Failed to load courses from JSON: {str(e)}")
        return None

def sync_course_to_json(course_id):
    """Sync a single course to JSON immediately after database operation"""
    try:
        # For now, just trigger a full courses backup
        # In the future, this could be optimized to update just one course
        return backup_courses_to_json()
    except Exception as e:
        logger.error(f"Failed to sync course {course_id} to JSON: {str(e)}")
        return False

def restore_from_json_backup():
    """
    Restore users from JSON backup file to database
    Returns the number of users restored
    """
    try:
        json_file = get_json_file_path(USERS_JSON_FILE)
        
        if not os.path.exists(json_file):
            logger.info("No JSON backup file found for users")
            return 0
        
        with open(json_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        users = backup_data.get('users', [])
        if not users:
            logger.info("JSON backup file exists but contains no users")
            return 0
        
        conn = get_connection()
        restored_count = 0
        
        for user in users:
            try:
                # Check if user already exists
                existing = conn.execute(
                    'SELECT id FROM users WHERE email = ?',
                    [user['email']]
                ).fetchone()
                
                if existing:
                    logger.debug(f"User {user['email']} already exists, skipping")
                    continue
                
                # Insert user
                conn.execute('''
                    INSERT INTO users (id, email, hashed_password, role)
                    VALUES (?, ?, ?, ?)
                ''', [user['id'], user['email'], user['hashed_password'], user['role']])
                
                restored_count += 1
                logger.debug(f"Restored user: {user['email']}")
                
            except Exception as user_error:
                logger.warning(f"Failed to restore user {user.get('email', 'unknown')}: {str(user_error)}")
                continue
        
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully restored {restored_count} users from JSON backup")
        return restored_count
        
    except Exception as e:
        logger.error(f"Error restoring users from JSON backup: {str(e)}")
        return 0
