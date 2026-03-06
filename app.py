from flask import Flask, render_template, request, jsonify
from google.cloud import firestore, storage
from firebase_admin import auth, initialize_app, credentials
import os
from datetime import datetime
import hashlib

# Initialize Firebase Admin
cred = credentials.Certificate(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
initialize_app(cred)

app = Flask(__name__)
app.config.from_object('config')

# Initialize Firestore
db = firestore.Client()

# Initialize Storage Manager
from storage_manager import StorageManager
storage_manager = StorageManager()

@app.route('/')
def index():
    """Home page accessible globally"""
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register_user():
    """Register new user"""
    data = request.json
    
    try:
        # Create Firebase Auth user
        user = auth.create_user(
            email=data['email'],
            password=data['password'],
            display_name=data.get('display_name', '')
        )
        
        # Store user profile in Firestore
        user_doc = {
            'uid': user.uid,
            'email': data['email'],
            'display_name': data.get('display_name', ''),
            'created_at': datetime.utcnow(),
            'storage_used_mb': 0,
            'post_count': 0,
            'profile_picture': None
        }
        
        db.collection('users').document(user.uid).set(user_doc)
        
        return jsonify({
            'success': True,
            'uid': user.uid,
            'message': 'User registered successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/create-post', methods=['POST'])
def create_post():
    """Create a new post with media"""
    try:
        # Verify user
        id_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        
        # Get post data
        title = request.form.get('title')
        content = request.form.get('content')
        
        # Handle file upload if present
        media_urls = []
        if 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                # Upload to GCS with auto-extension
                url = storage_manager.upload_file(
                    file=file,
                    user_id=user_id,
                    content_type='post'
                )
                media_urls.append(url)
        
        # Store post in Firestore
        post_data = {
            'user_id': user_id,
            'title': title,
            'content': content,
            'media_urls': media_urls,
            'created_at': datetime.utcnow(),
            'likes': 0,
            'comments_count': 0,
            'views': 0
        }
        
        post_ref = db.collection('posts').add(post_data)
        
        # Update user's post count
        user_ref = db.collection('users').document(user_id)
        user_ref.update({
            'post_count': firestore.Increment(1)
        })
        
        return jsonify({
            'success': True,
            'post_id': post_ref[1].id,
            'media_urls': media_urls
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Get all posts (globally accessible)"""
    try:
        posts = []
        posts_ref = db.collection('posts').order_by('created_at', direction=firestore.Query.DESCENDING).limit(50)
        
        for doc in posts_ref.stream():
            post = doc.to_dict()
            post['id'] = doc.id
            posts.append(post)
        
        return jsonify({'posts': posts}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)