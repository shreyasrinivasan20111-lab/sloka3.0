"""
Unified database interface that switches between DuckDB and PostgreSQL
based on environment configuration
"""

import os
from backend.logger import logger

def use_postgres():
    """Check if we should use PostgreSQL based on environment"""
    return bool(os.environ.get('DATABASE_URL') or (
        os.environ.get('DB_HOST') and 
        os.environ.get('DB_NAME') and 
        os.environ.get('DB_USER') and 
        os.environ.get('DB_PASSWORD')
    ))

def get_connection():
    """Get database connection - PostgreSQL for production, DuckDB for development"""
    if use_postgres():
        try:
            from backend.database_postgres import get_postgres_connection
            return get_postgres_connection()
        except ImportError:
            logger.warning("PostgreSQL dependencies not installed, falling back to DuckDB")
            from backend.database import get_connection as get_duck_connection
            return get_duck_connection()
        except Exception as e:
            logger.error(f"PostgreSQL connection failed, falling back to DuckDB: {str(e)}")
            from backend.database import get_connection as get_duck_connection
            return get_duck_connection()
    else:
        from backend.database import get_connection as get_duck_connection
        return get_duck_connection()

def init_database():
    """Initialize database - PostgreSQL for production, DuckDB for development"""
    if use_postgres():
        try:
            from backend.database_postgres import init_postgres_database
            return init_postgres_database()
        except ImportError:
            logger.warning("PostgreSQL dependencies not installed, using DuckDB")
            from backend.database import init_database as init_duck_database
            return init_duck_database()
        except Exception as e:
            logger.error(f"PostgreSQL initialization failed, using DuckDB: {str(e)}")
            from backend.database import init_database as init_duck_database
            return init_duck_database()
    else:
        from backend.database import init_database as init_duck_database
        return init_duck_database()

class DatabaseConnection:
    """Database connection wrapper that handles SQL differences between DuckDB and PostgreSQL"""
    
    def __init__(self):
        self.conn = get_connection()
        self.is_postgres = use_postgres()
    
    def execute(self, query, params=None):
        """Execute query with parameter binding differences handled"""
        if self.is_postgres:
            # PostgreSQL uses %s for parameters
            if params:
                # Convert list parameters to tuple for PostgreSQL
                if isinstance(params, list):
                    params = tuple(params)
                cursor = self.conn.cursor()
                cursor.execute(query, params)
                return cursor
            else:
                cursor = self.conn.cursor()
                cursor.execute(query)
                return cursor
        else:
            # DuckDB uses ? for parameters
            return self.conn.execute(query, params or [])
    
    def fetchall(self, cursor_or_result):
        """Fetch all results handling cursor differences"""
        if self.is_postgres:
            return cursor_or_result.fetchall()
        else:
            return cursor_or_result.fetchall()
    
    def fetchone(self, cursor_or_result):
        """Fetch one result handling cursor differences"""
        if self.is_postgres:
            result = cursor_or_result.fetchone()
            return result if result else None
        else:
            return cursor_or_result.fetchone()
    
    def commit(self):
        """Commit transaction"""
        self.conn.commit()
    
    def close(self):
        """Close connection"""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
        self.close()

def get_unified_connection():
    """Get a unified database connection wrapper"""
    return DatabaseConnection()

if __name__ == '__main__':
    print(f"Database mode: {'PostgreSQL' if use_postgres() else 'DuckDB'}")
    init_database()
