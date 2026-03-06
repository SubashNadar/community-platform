from google.cloud import storage, firestore
import os
from datetime import datetime
import logging

class StorageManager:
    def __init__(self):
        self.storage_client = storage.Client()
        self.db = firestore.Client()
        self.current_bucket_index = int(os.getenv('CURRENT_BUCKET_INDEX', 1))
        self.bucket_prefix = os.getenv('GCS_BUCKET_PREFIX')
        self.max_bucket_size_gb = int(os.getenv('MAX_BUCKET_SIZE_GB', 1000))
        self.warning_threshold = int(os.getenv('STORAGE_WARNING_THRESHOLD', 80))
        self.critical_threshold = int(os.getenv('STORAGE_CRITICAL_THRESHOLD', 95))
        self.max_buckets = int(os.getenv('MAX_BUCKETS', 100))
        
        self.current_bucket = self._get_or_create_bucket()
        
    def _get_or_create_bucket(self):
        """Get current bucket or create new one"""
        bucket_name = f"{self.bucket_prefix}{str(self.current_bucket_index).zfill(3)}"
        
        try:
            bucket = self.storage_client.bucket(bucket_name)
            if not bucket.exists():
                bucket = self._create_new_bucket(bucket_name)
            return bucket
        except Exception as e:
            logging.error(f"Error getting bucket: {e}")
            return self._create_new_bucket(bucket_name)
    
    def _create_new_bucket(self, bucket_name):
        """Create a new storage bucket"""
        bucket = self.storage_client.bucket(bucket_name)
        bucket.location = os.getenv('GCS_REGION', 'us-central1')
        bucket.storage_class = os.getenv('GCS_STORAGE_CLASS', 'STANDARD')
        
        # Enable versioning for data safety
        bucket.versioning_enabled = True
        
        # Set CORS for web access
        bucket.cors = [
            {
                "origin": ["*"],  # Allow all origins for global access
                "method": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "responseHeader": ["Content-Type", "Authorization"],
                "maxAgeSeconds": 3600
            }
        ]
        
        # Create bucket
        bucket = self.storage_client.create_bucket(bucket)
        
        # Log bucket creation
        self._log_bucket_creation(bucket_name)
        
        return bucket
    
    def _check_storage_capacity(self):
        """Check current storage usage and auto-extend if needed"""
        try:
            # Get current bucket stats
            total_size = 0
            file_count = 0
            
            for blob in self.current_bucket.list_blobs():
                total_size += blob.size
                file_count += 1
            
            # Convert to GB
            used_gb = total_size / (1024 ** 3)
            usage_percent = (used_gb / self.max_bucket_size_gb) * 100
            
            # Store metrics in Firestore
            metrics = {
                'bucket_name': self.current_bucket.name,
                'used_gb': used_gb,
                'max_gb': self.max_bucket_size_gb,
                'usage_percent': usage_percent,
                'file_count': file_count,
                'timestamp': datetime.utcnow()
            }
            
            self.db.collection('storage_metrics').add(metrics)
            
            # Check if we need to extend
            if usage_percent >= self.critical_threshold:
                self._extend_storage()
            elif usage_percent >= self.warning_threshold:
                self._send_storage_warning(usage_percent)
            
            return usage_percent
            
        except Exception as e:
            logging.error(f"Error checking storage: {e}")
            return 0
    
    def _extend_storage(self):
        """Automatically extend storage by creating new bucket"""
        if self.current_bucket_index >= self.max_buckets:
            self._send_critical_alert("Maximum bucket limit reached!")
            return False
        
        try:
            # Increment bucket index
            self.current_bucket_index += 1
            
            # Create new bucket
            new_bucket_name = f"{self.bucket_prefix}{str(self.current_bucket_index).zfill(3)}"
            self.current_bucket = self._create_new_bucket(new_bucket_name)
            
            # Update environment variable
            os.environ['CURRENT_BUCKET_INDEX'] = str(self.current_bucket_index)
            
            # Log extension
            self.db.collection('storage_extensions').add({
                'old_bucket_index': self.current_bucket_index - 1,
                'new_bucket_index': self.current_bucket_index,
                'new_bucket_name': new_bucket_name,
                'timestamp': datetime.utcnow(),
                'reason': 'auto_extension'
            })
            
            self._send_notification(f"Storage extended: New bucket {new_bucket_name} created")
            return True
            
        except Exception as e:
            logging.error(f"Error extending storage: {e}")
            self._send_critical_alert(f"Failed to extend storage: {e}")
            return False
    
    def upload_file(self, file, user_id, content_type='general'):
        """Upload file with automatic storage management"""
        try:
            # Check storage capacity before upload
            self._check_storage_capacity()
            
            # Generate unique filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"{user_id}/{content_type}/{timestamp}_{file.filename}"
            
            # Upload to current bucket
            blob = self.current_bucket.blob(filename)
            blob.upload_from_file(file, content_type=file.content_type)
            
            # Make publicly accessible
            blob.make_public()
            
            # Update user's storage usage
            self._update_user_storage(user_id, blob.size)
            
            # Return public URL
            return blob.public_url
            
        except Exception as e:
            logging.error(f"Upload error: {e}")
            # Try to extend storage and retry
            if "quota" in str(e).lower() or "space" in str(e).lower():
                if self._extend_storage():
                    return self.upload_file(file, user_id, content_type)
            raise e
    
    def _update_user_storage(self, user_id, size_bytes):
        """Update user's storage usage"""
        size_mb = size_bytes / (1024 * 1024)
        user_ref = self.db.collection('users').document(user_id)
        user_ref.update({
            'storage_used_mb': firestore.Increment(size_mb)
        })
    
    def _send_storage_warning(self, usage_percent):
        """Send warning notification"""
        message = f"Storage warning: {usage_percent:.1f}% used in bucket {self.current_bucket.name}"
        logging.warning(message)
        # Implement email/Slack notification here
    
    def _send_critical_alert(self, message):
        """Send critical alert"""
        logging.critical(message)
        # Implement email/Slack notification here
    
    def _send_notification(self, message):
        """Send general notification"""
        logging.info(message)
        # Implement email/Slack notification here
    
    def _log_bucket_creation(self, bucket_name):
        """Log bucket creation in Firestore"""
        self.db.collection('storage_buckets').add({
            'bucket_name': bucket_name,
            'bucket_index': self.current_bucket_index,
            'created_at': datetime.utcnow(),
            'status': 'active',
            'region': os.getenv('GCS_REGION', 'us-central1')
        })
    
    def get_storage_stats(self):
        """Get overall storage statistics"""
        stats = {
            'total_buckets': self.current_bucket_index,
            'max_buckets': self.max_buckets,
            'current_bucket': self.current_bucket.name,
            'buckets': []
        }
        
        # Get stats for all buckets
        for i in range(1, self.current_bucket_index + 1):
            bucket_name = f"{self.bucket_prefix}{str(i).zfill(3)}"
            try:
                bucket = self.storage_client.bucket(bucket_name)
                if bucket.exists():
                    size = sum(blob.size for blob in bucket.list_blobs())
                    stats['buckets'].append({
                        'name': bucket_name,
                        'size_gb': size / (1024 ** 3),
                        'status': 'active'
                    })
            except:
                pass
        
        return stats