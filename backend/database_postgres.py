"""
PostgreSQL database module for persistent storage
This replaces the local DuckDB with Supabase/PostgreSQL for production
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash
from backend.logger import logger

def get_postgres_connection():
    """Get PostgreSQL connection using environment variables"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            # Construct from individual components if DATABASE_URL not set
            host = os.environ.get('DB_HOST')
            port = os.environ.get('DB_PORT', '5432')
            database = os.environ.get('DB_NAME')
            user = os.environ.get('DB_USER')
            password = os.environ.get('DB_PASSWORD')
            
            if not all([host, database, user, password]):
                raise ValueError("Database connection parameters not set in environment variables")
            
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        # Parse SSL requirement for production databases
        sslmode = 'require' if 'supabase.co' in database_url or 'neon.db' in database_url else 'prefer'
        
        conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor,
            sslmode=sslmode
        )
        
        return conn
        
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {str(e)}")
        raise

def init_postgres_database():
    """Initialize PostgreSQL database with tables and sample data"""
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        logger.info("Initializing PostgreSQL database...")
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'student')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                content_richtext TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create assigned_courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assigned_courses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                UNIQUE(user_id, course_id)
            )
        ''')
        
        # Create files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id SERIAL PRIMARY KEY,
                course_id INTEGER NOT NULL,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            )
        ''')
        
        # Check if sample data is needed
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()['count']
        
        if user_count == 0:
            # Add sample users
            admin_pass = generate_password_hash('admin123', method='pbkdf2:sha256')
            student1_pass = generate_password_hash('student123', method='pbkdf2:sha256')
            student2_pass = generate_password_hash('student123', method='pbkdf2:sha256')
            
            cursor.execute('''
                INSERT INTO users (email, hashed_password, role) VALUES
                (%s, %s, 'admin'),
                (%s, %s, 'student'),
                (%s, %s, 'student')
            ''', [
                'admin@example.com', admin_pass,
                'student1@example.com', student1_pass,
                'student2@example.com', student2_pass
            ])
            
            logger.info("Sample users created in PostgreSQL:")
            logger.info("  Admin - email: admin@example.com, password: admin123")
            logger.info("  Student1 - email: student1@example.com, password: student123")
            logger.info("  Student2 - email: student2@example.com, password: student123")
        else:
            logger.info(f"PostgreSQL database already has {user_count} users - skipping sample data")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ PostgreSQL database initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL initialization failed: {str(e)}")
        return False

def migrate_duckdb_to_postgres():
    """Migrate existing DuckDB data to PostgreSQL"""
    try:
        # Import DuckDB functions
        from backend.database import get_connection as get_duck_connection
        
        logger.info("Starting migration from DuckDB to PostgreSQL...")
        
        # Get data from DuckDB
        duck_conn = get_duck_connection()
        
        users = duck_conn.execute('SELECT * FROM users').fetchall()
        courses = duck_conn.execute('SELECT * FROM courses').fetchall()
        assignments = duck_conn.execute('SELECT * FROM assigned_courses').fetchall()
        files = duck_conn.execute('SELECT * FROM files').fetchall()
        
        duck_conn.close()
        
        # Insert into PostgreSQL
        pg_conn = get_postgres_connection()
        cursor = pg_conn.cursor()
        
        # Clear existing data
        cursor.execute('DELETE FROM files')
        cursor.execute('DELETE FROM assigned_courses')
        cursor.execute('DELETE FROM courses')
        cursor.execute('DELETE FROM users')
        
        # Reset sequences
        cursor.execute('ALTER SEQUENCE users_id_seq RESTART WITH 1')
        cursor.execute('ALTER SEQUENCE courses_id_seq RESTART WITH 1')
        cursor.execute('ALTER SEQUENCE assigned_courses_id_seq RESTART WITH 1')
        cursor.execute('ALTER SEQUENCE files_id_seq RESTART WITH 1')
        
        # Insert users
        for user in users:
            cursor.execute('''
                INSERT INTO users (id, email, hashed_password, role, created_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', [user[0], user[1], user[2], user[3], user[4]])
        
        # Insert courses
        for course in courses:
            cursor.execute('''
                INSERT INTO courses (id, title, description, content_richtext, created_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', [course[0], course[1], course[2], course[3], course[4]])
        
        # Insert assignments
        for assignment in assignments:
            cursor.execute('''
                INSERT INTO assigned_courses (id, user_id, course_id, assigned_at)
                VALUES (%s, %s, %s, %s)
            ''', [assignment[0], assignment[1], assignment[2], assignment[3]])
        
        # Insert files
        for file_record in files:
            cursor.execute('''
                INSERT INTO files (id, course_id, filename, file_path, uploaded_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', [file_record[0], file_record[1], file_record[2], file_record[3], file_record[4]])
        
        # Update sequences to continue from max ID
        if users:
            cursor.execute('SELECT setval(\'users_id_seq\', (SELECT MAX(id) FROM users))')
        if courses:
            cursor.execute('SELECT setval(\'courses_id_seq\', (SELECT MAX(id) FROM courses))')
        if assignments:
            cursor.execute('SELECT setval(\'assigned_courses_id_seq\', (SELECT MAX(id) FROM assigned_courses))')
        if files:
            cursor.execute('SELECT setval(\'files_id_seq\', (SELECT MAX(id) FROM files))')
        
        pg_conn.commit()
        cursor.close()
        pg_conn.close()
        
        logger.info(f"✅ Migration completed! Migrated {len(users)} users, {len(courses)} courses, {len(assignments)} assignments, {len(files)} files")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == '__main__':
    init_postgres_database()
