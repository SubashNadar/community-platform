from google.cloud import storage
from google.oauth2 import service_account
from google.api_core import exceptions
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import logging
import json

class CloudStorage:
    def __init__(self):
        # Google Cloud Storage configuration
        self.project_id = os.environ.get('GCS_PROJECT_ID')
        self.bucket_prefix = os.environ.get('BUCKET_PREFIX', 'community-platform-bucket')
        self.current_bucket_index = int(os.environ.get('CURRENT_BUCKET_INDEX', 1))
        self.max_buckets = int(os.environ.get('STORAGE_MAX_BUCKETS', 10))
        self.storage_quota_gb = float(os.environ.get('MAX_SIZE_PER_BUCKET_GB', 100))
        self.critical_threshold = float(os.environ.get('STORAGE_CRITICAL_THRESHOLD', 95))
        
        # Initialize GCS client
        credentials_path = os.environ.get('GCS_CREDENTIALS_PATH')
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            self.client = storage.Client(
                project=self.project_id,
                credentials=credentials
            )
        else:
            # Use default credentials (for Google Cloud environments)
            self.client = storage.Client(project=self.project_id)
        
        # Get or create current bucket
        self.current_bucket_name = f"{self.bucket_prefix}-{self.current_bucket_index}"
        self.current_bucket = self._get_or_create_bucket(self.current_bucket_name)
        
        # Public URL pattern
        self.public_url_pattern = os.environ.get('GCS_PUBLIC_URL', 
            f"https://storage.googleapis.com/{self.current_bucket_name}")
    
    def _get_or_create_bucket(self, bucket_name):
        """Get existing bucket or create new one"""
        try:
            bucket = self.client.bucket(bucket_name)
            if not bucket.exists():
                bucket = self.client.create_bucket(
                    bucket_name,
                    location=os.environ.get('GCS_LOCATION', 'us-central1')
                )
                # Set bucket to public read
                bucket.make_public(recursive=True, future=True)
                logging.info(f"Created new bucket: {bucket_name}")
                
                # Set lifecycle rules for cost optimization
                bucket.lifecycle_rules = [{
                    'action': {'type': 'SetStorageClass', 'storageClass': 'NEARLINE'},
                    'condition': {'age': 30}
                }]
                bucket.patch()
            return bucket
        except exceptions.Conflict:
            # Bucket already exists
            return self.client.bucket(bucket_name)
        except Exception as e:
            logging.error(f"Error accessing bucket {bucket_name}: {e}")
            raise
    
    def _check_bucket_usage(self):
        """Check current bucket usage"""
        total_size = 0
        file_count = 0
        
        try:
            for blob in self.current_bucket.list_blobs():
                total_size += blob.size
                file_count += 1
        except Exception as e:
            logging.error(f"Error checking bucket usage: {e}")
            return {'size_gb': 0, 'percentage': 0, 'file_count': 0}
        
        size_gb = total_size / (1024 ** 3)
        percentage = (size_gb / self.storage_quota_gb) * 100
        
        return {
            'size_gb': size_gb,
            'percentage': percentage,
            'file_count': file_count
        }
    
    def _extend_storage(self):
        """Create new bucket when current is full"""
        if self.current_bucket_index >= self.max_buckets:
            logging.error("Maximum number of buckets reached!")
            return False
        
        self.current_bucket_index += 1
        new_bucket_name = f"{self.bucket_prefix}-{self.current_bucket_index}"
        
        try:
            self.current_bucket = self._get_or_create_bucket(new_bucket_name)
            self.current_bucket_name = new_bucket_name
            self.public_url_pattern = f"https://storage.googleapis.com/{new_bucket_name}"
            
            # Update environment variable or config file
            self._update_config()
            
            logging.info(f"Storage extended to bucket: {new_bucket_name}")
            return True
        except Exception as e:
            logging.error(f"Failed to extend storage: {e}")
            return False
    
    def _update_config(self):
        """Update configuration with new bucket index"""
        config_file = '.env.runtime'
        try:
            # Read existing config
            config = {}
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            config[key] = value
            
            # Update bucket index
            config['CURRENT_BUCKET_INDEX'] = str(self.current_bucket_index)
            
            # Write back
            with open(config_file, 'w') as f:
                for key, value in config.items():
                    f.write(f"{key}={value}\n")
        except Exception as e:
            logging.error(f"Failed to update config: {e}")
    
    def upload_file(self, file_obj, folder='media'):
        """Upload file to GCS with automatic bucket extension"""
        try:
            # Check if we need to extend storage
            usage = self._check_bucket_usage()
            if usage['percentage'] >= self.critical_threshold:
                if not self._extend_storage():
                    raise Exception("Storage full and cannot extend")
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(file_obj.filename)
            blob_name = f"{folder}/{timestamp}_{filename}"
            
            # Upload to GCS
            blob = self.current_bucket.blob(blob_name)
            
            # Set content type
            content_type = file_obj.content_type or 'application/octet-stream'
            blob.content_type = content_type
            
            # Upload file
            file_obj.seek(0)  # Reset file pointer
            blob.upload_from_file(file_obj)
            
            # Make blob public
            blob.make_public()
            
            # Return public URL
            return blob.public_url
            
        except Exception as e:
            logging.error(f"Error uploading file: {e}")
            return None
    
    def delete_file(self, file_url):
        """Delete file from GCS"""
        try:
            # Extract bucket name and blob name from URL
            # URL format: https://storage.googleapis.com/bucket-name/folder/file.ext
            if 'storage.googleapis.com' in file_url:
                parts = file_url.split('storage.googleapis.com/')[-1].split('/', 1)
                if len(parts) == 2:
                    bucket_name, blob_name = parts
                    bucket = self.client.bucket(bucket_name)
                    blob = bucket.blob(blob_name)
                    blob.delete()
                    return True
            
            # Alternative URL format: https://bucket-name.storage.googleapis.com/folder/file.ext
            elif '.storage.googleapis.com' in file_url:
                bucket_name = file_url.split('.storage.googleapis.com')[0].split('//')[-1]
                blob_name = file_url.split('.storage.googleapis.com/')[-1]
                bucket = self.client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.delete()
                return True
                
        except Exception as e:
            logging.error(f"Error deleting file: {e}")
        
        return False
    
    def get_storage_stats(self):
        """Get storage statistics across all buckets"""
        stats = {
            'total_size_gb': 0,
            'total_files': 0,
            'buckets': [],
            'current_bucket': self.current_bucket_name,
            'max_buckets': self.max_buckets
        }
        
        for i in range(1, self.current_bucket_index + 1):
            bucket_name = f"{self.bucket_prefix}-{i}"
            try:
                bucket = self.client.bucket(bucket_name)
                if bucket.exists():
                    bucket_size = 0
                    bucket_files = 0
                    for blob in bucket.list_blobs():
                        bucket_size += blob.size
                        bucket_files += 1
                    
                    bucket_size_gb = bucket_size / (1024 ** 3)
                    stats['total_size_gb'] += bucket_size_gb
                    stats['total_files'] += bucket_files
                    stats['buckets'].append({
                        'name': bucket_name,
                        'size_gb': bucket_size_gb,
                        'files': bucket_files,
                        'usage_percentage': (bucket_size_gb / self.storage_quota_gb) * 100
                    })
            except Exception as e:
                logging.error(f"Error getting stats for bucket {bucket_name}: {e}")
        
        return stats
    
    def list_files(self, folder='media', limit=100):
        """List files from current bucket"""
        files = []
        try:
            blobs = self.current_bucket.list_blobs(prefix=folder, max_results=limit)
            for blob in blobs:
                files.append({
                    'name': blob.name,
                    'size': blob.size,
                    'url': blob.public_url,
                    'created': blob.time_created,
                    'content_type': blob.content_type
                })
        except Exception as e:
            logging.error(f"Error listing files: {e}")
        
        return files

# Initialize storage instance
storage = CloudStorage()
