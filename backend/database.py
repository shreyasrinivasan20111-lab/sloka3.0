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
    import os
    
    db_path = get_db_path()
    is_serverless = os.environ.get('VERCEL') == '1'
    
    # Check if database already exists and has data (to prevent data loss)
    database_exists = os.path.exists(db_path)
    
    conn = get_connection()
    
    # Always create tables if they don't exist (safe operation)
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

    # Create sequences for auto-increment IDs (safe operation)
    try:
        conn.execute('CREATE SEQUENCE IF NOT EXISTS users_id_seq START 1')
        conn.execute('CREATE SEQUENCE IF NOT EXISTS courses_id_seq START 1')
        conn.execute('CREATE SEQUENCE IF NOT EXISTS assigned_courses_id_seq START 1')
        conn.execute('CREATE SEQUENCE IF NOT EXISTS files_id_seq START 1')
    except:
        pass  # Sequences might already exist

    # Only add sample data if no users exist (prevents data loss)
    try:
        result = conn.execute('SELECT COUNT(*) FROM users').fetchone()
        user_count = result[0] if result else 0
        
        if user_count == 0:
            # Add sample admin and students only if database is completely empty
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
        else:
            if is_serverless:
                print(f"Database already has {user_count} users - skipping sample data creation")
            else:
                print(f"Database already initialized with {user_count} users")
                
    except Exception as e:
        print(f"Warning during user data check: {e}")

    conn.commit()
    conn.close()
    
    if is_serverless:
        print("Database initialized for serverless environment!")
    else:
        print("Database initialized successfully!")
    
    # Warning for serverless environments about data persistence
    if is_serverless:
        print("\n" + "="*80)
        print("⚠️  SERVERLESS ENVIRONMENT WARNING ⚠️")
        print("Data stored in local DuckDB will be lost on deployment restarts!")
        print("For production, consider using a persistent database service like:")
        print("- PostgreSQL (Supabase, Neon, PlanetScale)")
        print("- MongoDB Atlas")
        print("- Firebase Firestore")
        print("="*80 + "\n")

if __name__ == '__main__':
    init_database()
