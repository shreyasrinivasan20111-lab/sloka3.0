"""
Enhanced DuckDB persistence with multiple storage backends
Supports local files, network drives, and cloud storage
"""

import os
import duckdb
import shutil
import tempfile
from pathlib import Path
from backend.logger import logger

class PersistentDuckDBManager:
    """Manages DuckDB file persistence with multiple storage options"""
    
    def __init__(self):
        self.storage_type = self._detect_storage_type()
        self.db_path = self._get_database_path()
        self.is_cloud_enabled = self._check_cloud_support()
        
    def _detect_storage_type(self):
        """Detect the best available storage type"""
        # Check for mounted network drive (works with some serverless platforms)
        network_path = os.environ.get('NETWORK_DB_PATH')
        if network_path and os.path.exists(os.path.dirname(network_path)):
            return 'network'
        
        # Check for Vercel's persistent volume (if available)
        vercel_volume = os.environ.get('VERCEL_VOLUME_PATH')
        if vercel_volume and os.path.exists(vercel_volume):
            return 'vercel_volume'
        
        # Check for cloud storage credentials
        if (os.environ.get('BLOB_READ_WRITE_TOKEN') or 
            os.environ.get('AWS_ACCESS_KEY_ID') or 
            os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')):
            return 'cloud_sync'
        
        # Fallback to local (will work in development)
        return 'local'
    
    def _get_database_path(self):
        """Get the database file path based on storage type"""
        if self.storage_type == 'network':
            return os.environ.get('NETWORK_DB_PATH', '/mnt/network/student_courses.db')
        
        elif self.storage_type == 'vercel_volume':
            volume_path = os.environ.get('VERCEL_VOLUME_PATH', '/mnt/vercel')
            return os.path.join(volume_path, 'student_courses.db')
        
        elif self.storage_type == 'cloud_sync':
            # Use temporary file that syncs to cloud
            return os.path.join(tempfile.gettempdir(), 'student_courses_sync.db')
        
        else:
            # Local development
            from backend.config import get_config
            return get_config().DB_PATH
    
    def _check_cloud_support(self):
        """Check if cloud synchronization is available"""
        return (self.storage_type == 'cloud_sync' and 
                (os.environ.get('BLOB_READ_WRITE_TOKEN') is not None))
    
    def get_connection(self):
        """Get DuckDB connection with appropriate persistence"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # For cloud sync, try to download existing database first
            if self.storage_type == 'cloud_sync':
                self._sync_from_cloud()
            
            # Create connection
            conn = duckdb.connect(self.db_path)
            
            logger.info(f"DuckDB connected: {self.storage_type} storage at {self.db_path}")
            return conn
            
        except Exception as e:
            logger.error(f"DuckDB connection failed: {e}")
            # Emergency fallback to in-memory database
            logger.warning("Falling back to in-memory database")
            return duckdb.connect(':memory:')
    
    def _sync_from_cloud(self):
        """Download database from cloud storage (Vercel Blob focus)"""
        if not self.is_cloud_enabled:
            return False
        
        try:
            # Simple HTTP download for Vercel Blob
            blob_url = os.environ.get('BLOB_URL')
            if blob_url and not os.path.exists(self.db_path):
                import urllib.request
                urllib.request.urlretrieve(blob_url, self.db_path)
                logger.info("Downloaded database from Vercel Blob")
                return True
                
        except Exception as e:
            logger.debug(f"Cloud sync download failed (normal for new databases): {e}")
        
        return False
    
    def sync_to_cloud(self):
        """Upload database to cloud storage"""
        if not self.is_cloud_enabled or not os.path.exists(self.db_path):
            return False
        
        try:
            # Simple HTTP upload for Vercel Blob
            blob_name = os.environ.get('BLOB_NAME', 'student_courses.db')
            token = os.environ.get('BLOB_READ_WRITE_TOKEN')
            
            if not token:
                return False
            
            # Use urllib for minimal dependencies
            import urllib.request
            import urllib.parse
            
            with open(self.db_path, 'rb') as f:
                data = f.read()
            
            # Create upload request
            url = f"https://blob.vercel-storage.com/{blob_name}"
            req = urllib.request.Request(
                url, 
                data=data,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/octet-stream'
                },
                method='PUT'
            )
            
            # Upload file
            with urllib.request.urlopen(req) as response:
                if response.status in [200, 201]:
                    logger.info("Database synced to Vercel Blob")
                    return True
                    
        except Exception as e:
            logger.error(f"Cloud sync upload failed: {e}")
        
        return False
    
    def get_storage_info(self):
        """Get information about current storage configuration"""
        return {
            'storage_type': self.storage_type,
            'database_path': self.db_path,
            'is_persistent': self.storage_type in ['network', 'vercel_volume', 'cloud_sync'],
            'cloud_sync_enabled': self.is_cloud_enabled,
            'exists': os.path.exists(self.db_path) if self.db_path else False,
            'size_mb': round(os.path.getsize(self.db_path) / 1024 / 1024, 2) if os.path.exists(self.db_path or '') else 0
        }
    
    def auto_sync(self):
        """Automatically sync to cloud after database operations"""
        if self.storage_type == 'cloud_sync':
            # Sync in background (don't block the request)
            try:
                import threading
                sync_thread = threading.Thread(target=self.sync_to_cloud)
                sync_thread.daemon = True
                sync_thread.start()
            except:
                # If threading fails, sync synchronously
                self.sync_to_cloud()

# Global manager instance
persistent_db = PersistentDuckDBManager()

def get_persistent_connection():
    """Get DuckDB connection with best available persistence"""
    return persistent_db.get_connection()

def get_persistence_info():
    """Get information about database persistence"""
    return persistent_db.get_storage_info()

def sync_database():
    """Manually trigger database sync to cloud"""
    return persistent_db.sync_to_cloud()

def auto_sync_after_write():
    """Auto-sync database after write operations"""
    return persistent_db.auto_sync()
