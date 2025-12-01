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

def use_persistent_duckdb():
    """Check if we should use persistent DuckDB with external storage"""
    return bool(
        os.environ.get('NETWORK_DB_PATH') or 
        os.environ.get('VERCEL_VOLUME_PATH') or
        os.environ.get('BLOB_READ_WRITE_TOKEN') or
        os.environ.get('BLOB_URL')
    )

def get_connection():
    """Get database connection - PostgreSQL, Persistent DuckDB, or regular DuckDB"""
    if use_postgres():
        try:
            from backend.database_postgres import get_postgres_connection
            return get_postgres_connection()
        except ImportError:
            logger.warning("PostgreSQL dependencies not installed, falling back to DuckDB")
            # Fall through to DuckDB selection
        except Exception as e:
            logger.error(f"PostgreSQL connection failed, falling back to DuckDB: {str(e)}")
            # Fall through to DuckDB selection
    
    # Choose DuckDB type based on persistence configuration
    if use_persistent_duckdb():
        try:
            from backend.database_persistent import get_persistent_connection
            logger.info("Using persistent DuckDB with external storage")
            return get_persistent_connection()
        except Exception as e:
            logger.warning(f"Persistent DuckDB failed, using regular DuckDB: {str(e)}")
    
    # Fallback to regular DuckDB
    from backend.database import get_connection as get_duck_connection
    return get_duck_connection()

def init_database():
    """Initialize database - PostgreSQL, Persistent DuckDB, or regular DuckDB"""
    if use_postgres():
        try:
            from backend.database_postgres import init_postgres_database
            return init_postgres_database()
        except ImportError:
            logger.warning("PostgreSQL dependencies not installed, using DuckDB")
            # Fall through to DuckDB initialization
        except Exception as e:
            logger.error(f"PostgreSQL initialization failed, using DuckDB: {str(e)}")
            # Fall through to DuckDB initialization
    
    # Initialize appropriate DuckDB type
    from backend.database import init_database as init_duck_database
    result = init_duck_database()
    
    # If using persistent DuckDB, trigger initial sync
    if use_persistent_duckdb():
        try:
            from backend.database_persistent import auto_sync_after_write
            auto_sync_after_write()
            logger.info("Persistent DuckDB initialized with external storage sync")
        except Exception as e:
            logger.warning(f"Persistent DuckDB sync failed: {str(e)}")
    
    return result

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
        """Commit transaction and auto-sync if using persistent DuckDB"""
        self.conn.commit()
        
        # Auto-sync to cloud after writes if using persistent DuckDB
        if not self.is_postgres and use_persistent_duckdb():
            try:
                from backend.database_persistent import auto_sync_after_write
                auto_sync_after_write()
            except Exception as e:
                logger.debug(f"Auto-sync after commit failed: {e}")
    
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
    if use_postgres():
        print("🗄️ Database mode: PostgreSQL (External)")
    elif use_persistent_duckdb():
        print("🗄️ Database mode: DuckDB (Persistent External Storage)")
        try:
            from backend.database_persistent import get_persistence_info
            info = get_persistence_info()
            print(f"   Storage: {info['storage_type'].replace('_', ' ').title()}")
            print(f"   Path: {info['database_path']}")
            print(f"   Persistent: {'✅ Yes' if info['is_persistent'] else '❌ No'}")
            print(f"   Cloud Sync: {'✅ Enabled' if info.get('cloud_sync_enabled') else '❌ Disabled'}")
        except Exception as e:
            print(f"   Error getting storage info: {e}")
    else:
        print("🗄️ Database mode: DuckDB (Local)")
        print("   ⚠️ Data will be lost on serverless deployment restarts")
        print("   💡 See PERSISTENT_DUCKDB_SETUP.md for external storage options")
    
    init_database()
    print("✅ Database initialized successfully")
