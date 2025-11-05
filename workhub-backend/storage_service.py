"""
Cloud Storage Service for GCP Integration
Handles file uploads to Google Cloud Storage when USE_CLOUD_STORAGE is enabled
Falls back to local storage otherwise
"""

import os
import logging
from typing import Optional, BinaryIO
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

# Configuration
USE_CLOUD_STORAGE = os.environ.get('USE_CLOUD_STORAGE', 'false').lower() == 'true'
CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET')
GCP_PROJECT = os.environ.get('GCP_PROJECT')

# Lazy import Google Cloud Storage (only if needed)
if USE_CLOUD_STORAGE:
    try:
        from google.cloud import storage
        storage_client = storage.Client(project=GCP_PROJECT) if GCP_PROJECT else storage.Client()
    except Exception as e:
        logger.warning(f"Failed to initialize Google Cloud Storage client: {e}")
        storage_client = None
else:
    storage_client = None


class StorageService:
    """Unified storage service that works with both local and cloud storage"""
    
    @staticmethod
    def save_file(file: FileStorage, filename: str, subfolder: str = 'uploads') -> str:
        """
        Save a file to storage (local or cloud based on configuration)
        
        Args:
            file: The file object to save
            filename: The filename to use
            subfolder: Subdirectory/prefix for organizing files
            
        Returns:
            The file path or URL where the file was saved
        """
        if USE_CLOUD_STORAGE and storage_client and CLOUD_STORAGE_BUCKET:
            return StorageService._save_to_cloud(file, filename, subfolder)
        else:
            return StorageService._save_to_local(file, filename, subfolder)
    
    @staticmethod
    def _save_to_cloud(file: FileStorage, filename: str, subfolder: str) -> str:
        """Save file to Google Cloud Storage"""
        try:
            bucket = storage_client.bucket(CLOUD_STORAGE_BUCKET)
            blob_name = f"{subfolder}/{filename}"
            blob = bucket.blob(blob_name)
            
            # Upload file
            file.seek(0)  # Reset file pointer
            blob.upload_from_file(file, content_type=file.content_type)
            
            # Make blob publicly accessible (optional - adjust based on security needs)
            # For private files, you'll need to generate signed URLs
            # blob.make_public()
            
            # Return the Cloud Storage path (not public URL for security)
            file_path = f"gs://{CLOUD_STORAGE_BUCKET}/{blob_name}"
            logger.info(f"File uploaded to Cloud Storage: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error uploading to Cloud Storage: {e}")
            # Fallback to local storage
            logger.warning("Falling back to local storage")
            return StorageService._save_to_local(file, filename, subfolder)
    
    @staticmethod
    def _save_to_local(file: FileStorage, filename: str, subfolder: str) -> str:
        """Save file to local filesystem"""
        upload_folder = os.environ.get('UPLOAD_FOLDER', 'uploads')
        full_path = os.path.join(upload_folder, subfolder)
        
        # Create directory if it doesn't exist
        os.makedirs(full_path, exist_ok=True)
        
        file_path = os.path.join(full_path, filename)
        file.save(file_path)
        
        logger.info(f"File saved locally: {file_path}")
        return file_path
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            file_path: The path to the file (local path or gs:// URL)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if file_path.startswith('gs://'):
            return StorageService._delete_from_cloud(file_path)
        else:
            return StorageService._delete_from_local(file_path)
    
    @staticmethod
    def _delete_from_cloud(file_path: str) -> bool:
        """Delete file from Google Cloud Storage"""
        try:
            # Parse gs://bucket/path format
            path_parts = file_path.replace('gs://', '').split('/', 1)
            if len(path_parts) != 2:
                logger.error(f"Invalid Cloud Storage path: {file_path}")
                return False
            
            bucket_name, blob_name = path_parts
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            
            logger.info(f"File deleted from Cloud Storage: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from Cloud Storage: {e}")
            return False
    
    @staticmethod
    def _delete_from_local(file_path: str) -> bool:
        """Delete file from local filesystem"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted locally: {file_path}")
                return True
            else:
                logger.warning(f"File not found: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting local file: {e}")
            return False
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Check if a file exists in storage"""
        if file_path.startswith('gs://'):
            return StorageService._cloud_file_exists(file_path)
        else:
            return os.path.exists(file_path)
    
    @staticmethod
    def _cloud_file_exists(file_path: str) -> bool:
        """Check if file exists in Cloud Storage"""
        try:
            path_parts = file_path.replace('gs://', '').split('/', 1)
            if len(path_parts) != 2:
                return False
            
            bucket_name, blob_name = path_parts
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            return blob.exists()
            
        except Exception as e:
            logger.error(f"Error checking Cloud Storage file existence: {e}")
            return False
    
    @staticmethod
    def generate_signed_url(file_path: str, expiration_minutes: int = 60) -> Optional[str]:
        """
        Generate a signed URL for temporary access to a cloud storage file
        
        Args:
            file_path: The gs:// path to the file
            expiration_minutes: How long the URL should be valid
            
        Returns:
            A signed URL, or None if not using cloud storage or error occurs
        """
        if not file_path.startswith('gs://') or not storage_client:
            return None
        
        try:
            from datetime import timedelta
            
            path_parts = file_path.replace('gs://', '').split('/', 1)
            if len(path_parts) != 2:
                return None
            
            bucket_name, blob_name = path_parts
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            # Generate signed URL
            url = blob.generate_signed_url(
                expiration=timedelta(minutes=expiration_minutes),
                method='GET'
            )
            
            return url
            
        except Exception as e:
            logger.error(f"Error generating signed URL: {e}")
            return None


# Export singleton instance
storage_service = StorageService()

