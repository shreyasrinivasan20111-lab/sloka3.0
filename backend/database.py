import duckdb
import os
from werkzeug.security import generate_password_hash

def get_db_path():
    """Get database path from environment or use default"""
    from backend.config import get_config
    return get_config().DB_PATH

def get_connection():
    """Get a connection to the DuckDB database"""
    return duckdb.connect(get_db_path())

def init_database():
    """Initialize the database with tables and sample data"""
    conn = get_connection()

    # Create users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email VARCHAR UNIQUE NOT NULL,
            hashed_password VARCHAR NOT NULL,
            role VARCHAR NOT NULL CHECK (role IN ('admin', 'student')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create courses table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            title VARCHAR NOT NULL,
            description VARCHAR,
            content_richtext TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create assigned_courses table (many-to-many relationship)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS assigned_courses (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id),
            UNIQUE(user_id, course_id)
        )
    ''')

    # Create files table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            course_id INTEGER NOT NULL,
            filename VARCHAR NOT NULL,
            file_path VARCHAR NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    ''')

    # Create sequences for auto-increment IDs
    try:
        conn.execute('CREATE SEQUENCE IF NOT EXISTS users_id_seq START 1')
        conn.execute('CREATE SEQUENCE IF NOT EXISTS courses_id_seq START 1')
        conn.execute('CREATE SEQUENCE IF NOT EXISTS assigned_courses_id_seq START 1')
        conn.execute('CREATE SEQUENCE IF NOT EXISTS files_id_seq START 1')
    except:
        pass  # Sequences might already exist

    # Check if we need to add sample data
    result = conn.execute('SELECT COUNT(*) FROM users').fetchone()
    if result[0] == 0:
        # Add sample admin and students
        admin_pass = generate_password_hash('admin123', method='pbkdf2:sha256')
        student1_pass = generate_password_hash('student123', method='pbkdf2:sha256')
        student2_pass = generate_password_hash('student123', method='pbkdf2:sha256')

        conn.execute('''
            INSERT INTO users (id, email, hashed_password, role)
            VALUES
                (nextval('users_id_seq'), 'admin@example.com', ?, 'admin'),
                (nextval('users_id_seq'), 'student1@example.com', ?, 'student'),
                (nextval('users_id_seq'), 'student2@example.com', ?, 'student')
        ''', [admin_pass, student1_pass, student2_pass])

        print("Sample users created:")
        print("  Admin - email: admin@example.com, password: admin123")
        print("  Student1 - email: student1@example.com, password: student123")
        print("  Student2 - email: student2@example.com, password: student123")

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()
