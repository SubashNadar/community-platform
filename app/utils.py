import os
import uuid
from PIL import Image
from flask import current_app, flash
from werkzeug.utils import secure_filename
import json
from app import redis_client

# Optional imports with fallbacks
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    print("boto3 not available - S3 upload disabled")

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    print("python-magic not available - using basic file validation")

def allowed_file(filename):
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {
        'jpg', 'jpeg', 'png', 'gif', 'webp',
        'mp4', 'mov', 'avi', 'mkv',
        'pdf', 'txt', 'doc', 'docx'
    })
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        return 'image'
    elif ext in ['mp4', 'mov', 'avi', 'mkv']:
        return 'video'
    else:
        return 'document'

def generate_unique_filename(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"

def compress_image(image_path, max_size=(1920, 1080), quality=85):
    """Compress image to reduce file size and optimize for web"""
    try:
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if larger than max_size
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(image_path, optimize=True, quality=quality)
            return True
    except Exception as e:
        print(f"Error compressing image: {e}")
        return False

def upload_to_s3(file_path, filename, bucket_name):
    """Upload file to AWS S3"""
    if not HAS_BOTO3:
        return None, None
        
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY'),
            region_name=current_app.config.get('AWS_S3_REGION')
        )
        
        s3_key = f"uploads/{filename}"
        s3_client.upload_file(file_path, bucket_name, s3_key)
        
        # Generate URL
        s3_url = f"https://{bucket_name}.s3.{current_app.config.get('AWS_S3_REGION')}.amazonaws.com/{s3_key}"
        
        return s3_key, s3_url
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None, None

def cache_get(key):
    """Get value from Redis cache"""
    if not redis_client:
        return None
    try:
        value = redis_client.get(key)
        return json.loads(value) if value else None
    except:
        return None

def cache_set(key, value, timeout=300):
    """Set value in Redis cache with timeout (default 5 minutes)"""
    if not redis_client:
        return False
    try:
        redis_client.setex(key, timeout, json.dumps(value))
        return True
    except:
        return False

def cache_delete(key):
    """Delete key from Redis cache"""
    if not redis_client:
        return False
    try:
        redis_client.delete(key)
        return True
    except:
        return False

def validate_file_content(file_path):
    """Validate file content using python-magic or fallback to extension"""
    if not HAS_MAGIC:
        # Fallback to extension-based validation
        ext = file_path.rsplit('.', 1)[-1].lower() if '.' in file_path else ''
        allowed_exts = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg', 
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'mp4': 'video/mp4',
            'mov': 'video/quicktime',
            'avi': 'video/x-msvideo',
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        if ext in allowed_exts:
            return True, allowed_exts[ext]
        return False, None
        
    try:
        mime_type = magic.from_file(file_path, mime=True)
        
        # Define allowed MIME types
        allowed_mimes = {
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'video/mp4', 'video/quicktime', 'video/x-msvideo',
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        }
        
        return mime_type in allowed_mimes, mime_type
    except Exception as e:
        print(f"Error validating file: {e}")
        return False, None

def get_file_size_mb(file_path):
    """Get file size in MB"""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except OSError:
        return 0
