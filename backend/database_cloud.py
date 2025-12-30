"""
Cloud storage adapter for DuckDB file persistence
Supports AWS S3, Google Cloud Storage, and Vercel Blob
"""

import os
import duckdb
import tempfile
import shutil
from pathlib import Path
from backend.logger import logger

# Optional cloud storage imports
try:
    import boto3  # type: ignore
except ImportError:
    boto3 = None

try:
    from google.cloud import storage  # type: ignore
except ImportError:
    storage = None

try:
    import requests  # type: ignore
except ImportError:
    requests = None

class CloudDuckDBManager:
    """Manages DuckDB file storage in cloud services"""
    
    def __init__(self):
        self.storage_provider = self._detect_storage_provider()
        self.local_db_path = None
        
    def _detect_storage_provider(self):
        """Auto-detect available cloud storage provider"""
        if os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY'):
            return 'aws_s3'
        elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
            return 'gcs'
        elif os.environ.get('BLOB_READ_WRITE_TOKEN'):
            return 'vercel_blob'
        else:
            return 'local'
    
    def get_connection(self):
        """Get DuckDB connection with cloud sync"""
        try:
            # Download database file from cloud if needed
            local_path = self._ensure_local_database()
            
            # Create connection to local file
            conn = duckdb.connect(local_path)
            
            # Store path for later upload
            self.local_db_path = local_path
            
            return conn
            
        except Exception as e:
            logger.error(f"Cloud DuckDB connection failed: {e}")
            # Fallback to temporary local database
            temp_path = os.path.join(tempfile.gettempdir(), 'fallback_student_courses.db')
            self.local_db_path = temp_path
            return duckdb.connect(temp_path)
    
    def _ensure_local_database(self):
        """Download database from cloud or create local copy"""
        if self.storage_provider == 'local':
            # Use local file system
            from backend.config import get_config
            return get_config().DB_PATH
        
        # Create temporary local path
        temp_dir = tempfile.gettempdir()
        local_db_path = os.path.join(temp_dir, 'student_courses.db')
        
        # Try to download existing database
        if self._download_from_cloud(local_db_path):
            logger.info(f"Downloaded database from {self.storage_provider}")
        else:
            logger.info(f"No existing database found in {self.storage_provider}, will create new one")
        
        return local_db_path
    
    def _download_from_cloud(self, local_path):
        """Download database file from cloud storage"""
        try:
            if self.storage_provider == 'aws_s3':
                return self._download_from_s3(local_path)
            elif self.storage_provider == 'gcs':
                return self._download_from_gcs(local_path)
            elif self.storage_provider == 'vercel_blob':
                return self._download_from_vercel_blob(local_path)
            
            return False
            
        except Exception as e:
            logger.warning(f"Failed to download database from {self.storage_provider}: {e}")
            return False
    
    def _download_from_s3(self, local_path):
        """Download from AWS S3"""
        if boto3 is None:
            logger.warning("boto3 not installed for S3 support")
            return False
            
        try:
            s3 = boto3.client('s3')
            bucket = os.environ.get('S3_BUCKET', 'student-course-db')
            key = os.environ.get('S3_KEY', 'student_courses.db')
            
            s3.download_file(bucket, key, local_path)
            return True
            
        except Exception as e:
            logger.debug(f"S3 download failed (expected for new databases): {e}")
            return False
    
    def _download_from_gcs(self, local_path):
        """Download from Google Cloud Storage"""
        if storage is None:
            logger.warning("google-cloud-storage not installed for GCS support")
            return False
            
        try:
            client = storage.Client()
            bucket_name = os.environ.get('GCS_BUCKET', 'student-course-db')
            blob_name = os.environ.get('GCS_BLOB', 'student_courses.db')
            
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            blob.download_to_filename(local_path)
            return True
            
        except Exception as e:
            logger.debug(f"GCS download failed (expected for new databases): {e}")
            return False
    
    def _download_from_vercel_blob(self, local_path):
        """Download from Vercel Blob Storage"""
        if requests is None:
            logger.warning("requests not installed for Vercel Blob support")
            return False
            
        try:
            blob_url = os.environ.get('BLOB_URL')
            if not blob_url:
                # Construct URL if not provided
                blob_name = os.environ.get('BLOB_NAME', 'student_courses.db')
                blob_url = f"https://blob.vercel-storage.com/{blob_name}"
            
            token = os.environ.get('BLOB_READ_WRITE_TOKEN')
            
            response = requests.get(
                blob_url,
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Vercel Blob download failed (expected for new databases): {e}")
            return False
    
    def sync_to_cloud(self):
        """Upload current database to cloud storage"""
        if not self.local_db_path or self.storage_provider == 'local':
            return True
        
        try:
            if self.storage_provider == 'aws_s3':
                return self._upload_to_s3()
            elif self.storage_provider == 'gcs':
                return self._upload_to_gcs()
            elif self.storage_provider == 'vercel_blob':
                return self._upload_to_vercel_blob()
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to sync database to {self.storage_provider}: {e}")
            return False
    
    def _upload_to_s3(self):
        """Upload to AWS S3"""
        if boto3 is None:
            logger.warning("boto3 not installed for S3 support")
            return False
            
        try:
            s3 = boto3.client('s3')
            bucket = os.environ.get('S3_BUCKET', 'student-course-db')
            key = os.environ.get('S3_KEY', 'student_courses.db')
            
            s3.upload_file(self.local_db_path, bucket, key)
            logger.info("Database synced to S3")
            return True
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return False
    
    def _upload_to_gcs(self):
        """Upload to Google Cloud Storage"""
        if storage is None:
            logger.warning("google-cloud-storage not installed for GCS support")
            return False
            
        try:
            client = storage.Client()
            bucket_name = os.environ.get('GCS_BUCKET', 'student-course-db')
            blob_name = os.environ.get('GCS_BLOB', 'student_courses.db')
            
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            blob.upload_from_filename(self.local_db_path)
            logger.info("Database synced to Google Cloud Storage")
            return True
            
        except Exception as e:
            logger.error(f"GCS upload failed: {e}")
            return False
    
    def _upload_to_vercel_blob(self):
        """Upload to Vercel Blob Storage"""
        if requests is None:
            logger.warning("requests not installed for Vercel Blob support")
            return False
            
        try:
            with open(self.local_db_path, 'rb') as f:
                file_data = f.read()
            
            blob_name = os.environ.get('BLOB_NAME', 'student_courses.db')
            token = os.environ.get('BLOB_READ_WRITE_TOKEN')
            
            response = requests.put(
                f"https://blob.vercel-storage.com/{blob_name}",
                data=file_data,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/octet-stream'
                }
            )
            
            if response.status_code in [200, 201]:
                logger.info("Database synced to Vercel Blob Storage")
                return True
            else:
                logger.error(f"Vercel Blob upload failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Vercel Blob upload failed: {e}")
            return False
    
    def get_storage_info(self):
        """Get information about current storage setup"""
        return {
            'provider': self.storage_provider,
            'local_path': self.local_db_path,
            'persistent': self.storage_provider != 'local' or not os.environ.get('VERCEL'),
            'sync_available': self.storage_provider != 'local'
        }

# Global instance
cloud_db_manager = CloudDuckDBManager()

def get_cloud_connection():
    """Get DuckDB connection with cloud persistence"""
    return cloud_db_manager.get_connection()

def sync_database_to_cloud():
    """Manually sync database to cloud storage"""
    return cloud_db_manager.sync_to_cloud()
