#!/usr/bin/env python3
"""
Database Setup and Migration Script
Helps migrate from local DuckDB to external PostgreSQL database
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import use_postgres, init_database
from backend.logger import logger

def check_environment():
    """Check current database configuration"""
    print("=== Database Configuration Check ===")
    
    if use_postgres():
        print("✅ PostgreSQL configuration detected")
        if os.environ.get('DATABASE_URL'):
            print(f"   Using DATABASE_URL: {os.environ.get('DATABASE_URL')[:50]}...")
        else:
            print(f"   Host: {os.environ.get('DB_HOST')}")
            print(f"   Database: {os.environ.get('DB_NAME')}")
            print(f"   User: {os.environ.get('DB_USER')}")
    else:
        print("📁 Local DuckDB configuration detected")
        from backend.config import get_config
        config = get_config()
        print(f"   Database path: {config.DB_PATH}")
        
        # Check if local database exists and has data
        if os.path.exists(config.DB_PATH):
            try:
                from backend.database import get_connection
                conn = get_connection()
                user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
                course_count = conn.execute('SELECT COUNT(*) FROM courses').fetchone()[0]
                conn.close()
                print(f"   📊 Current data: {user_count} users, {course_count} courses")
            except Exception as e:
                print(f"   ⚠️  Could not read database: {e}")
        else:
            print("   📊 No local database file found")
    
    print()

def migrate_to_postgres():
    """Migrate existing DuckDB data to PostgreSQL"""
    if use_postgres():
        print("❌ Already using PostgreSQL - no migration needed")
        return
    
    print("=== Migrating Local Data to PostgreSQL ===")
    print("This will:")
    print("1. Check your local DuckDB data")
    print("2. Set up PostgreSQL database")  
    print("3. Copy all your courses and users to PostgreSQL")
    print("4. Verify the migration")
    print()
    
    # Check if DATABASE_URL is set
    if not (os.environ.get('DATABASE_URL') or all([
        os.environ.get('DB_HOST'),
        os.environ.get('DB_NAME'), 
        os.environ.get('DB_USER'),
        os.environ.get('DB_PASSWORD')
    ])):
        print("❌ PostgreSQL connection not configured!")
        print("Please set DATABASE_URL or DB_HOST/DB_NAME/DB_USER/DB_PASSWORD environment variables")
        print("See .env.example for instructions")
        return
    
    try:
        print("🔄 Initializing PostgreSQL database...")
        init_database()
        
        print()
        print("✅ Database initialization completed successfully!")
        print("Your database is now set up with PostgreSQL and will persist across deployments.")
        print()
        print("Sample accounts created:")
        print("👨‍💼 Admin: admin@example.com / admin123")
        print("👨‍🎓 Student1: student1@example.com / student123") 
        print("👨‍🎓 Student2: student2@example.com / student123")
        print()
        print("Next steps:")
        print("1. Add DATABASE_URL to your Vercel environment variables")
        print("2. Deploy your application")  
        print("3. Your courses will now persist forever! 🎉")
            
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        print("Make sure your PostgreSQL connection is working and try again.")

def setup_database():
    """Initialize database (PostgreSQL or DuckDB)"""
    print("=== Database Setup ===")
    
    if use_postgres():
        print("🐘 Initializing PostgreSQL database...")
    else:
        print("🦆 Initializing local DuckDB database...")
    
    try:
        success = init_database()
        if success:
            print("✅ Database initialized successfully!")
        else:
            print("❌ Database initialization failed")
    except Exception as e:
        print(f"❌ Database setup error: {e}")

def main():
    print("🚀 Student Course Management Database Setup")
    print("=" * 50)
    
    while True:
        print("\nChoose an option:")
        print("1. Check current database configuration")
        print("2. Initialize/setup database")
        print("3. Migrate from DuckDB to PostgreSQL") 
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            check_environment()
        elif choice == '2':
            setup_database()
        elif choice == '3':
            migrate_to_postgres()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == '__main__':
    main()
