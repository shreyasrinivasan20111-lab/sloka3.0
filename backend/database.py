"""
Simplified PostgreSQL-only database module for Sloka Course Management System
This module handles all database operations using Vercel PostgreSQL.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash
from backend.logger import logger

def get_connection():
    """Get PostgreSQL connection using Vercel environment variables"""
    try:
        # Vercel provides DATABASE_URL automatically for PostgreSQL
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            # Fallback to individual components if DATABASE_URL not set
            host = os.environ.get('DB_HOST')
            port = os.environ.get('DB_PORT', '5432')
            database = os.environ.get('DB_NAME') 
            user = os.environ.get('DB_USER')
            password = os.environ.get('DB_PASSWORD')
            
            if not all([host, database, user, password]):
                raise ValueError("Database connection parameters not set. Please configure DATABASE_URL or individual DB_* environment variables.")
            
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        # Use SSL for production databases (required by Vercel Postgres)
        sslmode = 'require'
        
        conn = psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor,
            sslmode=sslmode
        )
        
        logger.debug("✅ PostgreSQL connection established")
        return conn
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {str(e)}")
        raise

def init_database():
    """Initialize PostgreSQL database with tables and sample data"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        logger.info("🔧 Initializing PostgreSQL database...")
        
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
                lyrics TEXT,
                audio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create assigned_courses table (many-to-many relationship)
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
                file_path VARCHAR(255) NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            )
        ''')

        # Check if sample data already exists
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()['count']
        
        if user_count == 0:
            logger.info("📦 Creating sample data...")
            
            # Add sample admin and students
            admin_pass = generate_password_hash('admin123', method='pbkdf2:sha256')
            student1_pass = generate_password_hash('student123', method='pbkdf2:sha256') 
            student2_pass = generate_password_hash('student123', method='pbkdf2:sha256')

            cursor.execute('''
                INSERT INTO users (email, hashed_password, role)
                VALUES
                    (%s, %s, 'admin'),
                    (%s, %s, 'student'),
                    (%s, %s, 'student')
            ''', [
                'admin@example.com', admin_pass,
                'student1@example.com', student1_pass,
                'student2@example.com', student2_pass
            ])

            # Add sample course
            cursor.execute('''
                INSERT INTO courses (title, description, content_richtext, lyrics)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            ''', [
                'Sample Sloka Course',
                'A sample course to demonstrate the Sloka Course Management System',
                '<h2>Welcome to Sloka Course Management</h2><p>This is a sample course with rich text content.</p>',
                'Sample lyrics content for the course'
            ])
            
            course_result = cursor.fetchone()
            if course_result:
                course_id = course_result['id']
                
                # Assign course to students
                cursor.execute('''
                    INSERT INTO assigned_courses (user_id, course_id)
                    SELECT u.id, %s FROM users u WHERE u.role = 'student'
                ''', [course_id])

            logger.info("✅ Sample data created:")
            logger.info("   👨‍💼 Admin: admin@example.com / admin123")
            logger.info("   👨‍🎓 Student1: student1@example.com / student123")
            logger.info("   👨‍🎓 Student2: student2@example.com / student2123")
            logger.info("   📚 Sample course assigned to students")
            
        else:
            logger.info(f"✅ Database already initialized with {user_count} users")

        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("🎉 PostgreSQL database initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        raise

def ensure_tables_exist():
    """Ensure all required database tables exist"""
    return init_database()

def get_unified_db_path():
    """Return database connection info for compatibility"""
    database_url = os.environ.get('DATABASE_URL', 'PostgreSQL via DATABASE_URL')
    return database_url

def execute_query(query, params=None, fetch_one=False, fetch_all=None):
    """
    Execute a query and return results
    Handles both PostgreSQL cursor-based and direct execution patterns
    Defaults to fetch_all=True for SELECT statements, unless fetch_one=True is specified
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Execute the query
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Auto-detect if we should fetch results based on query type
        query_upper = query.strip().upper()
        is_select = query_upper.startswith('SELECT')
        
        # Handle different return types
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all is True or (fetch_all is None and is_select):
            result = cursor.fetchall()
        else:
            result = None
            
        # Commit for write operations
        if query_upper.startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP')):
            conn.commit()
            
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Database query error: {str(e)} | Query: {query[:100]}...")
        if conn:
            conn.rollback()
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        raise

def use_postgres():
    """Always return True since we only use PostgreSQL now"""
    return True

def use_persistent_duckdb():
    """Always return False since we removed DuckDB support"""
    return False

if __name__ == '__main__':
    logger.info("🗄️  Database mode: PostgreSQL (Vercel)")
    database_url = os.environ.get('DATABASE_URL', 'Not configured')
    logger.info(f"   Connection: {database_url[:50]}...")
    
    try:
        init_database()
        logger.info("✅ Database test successful")
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
