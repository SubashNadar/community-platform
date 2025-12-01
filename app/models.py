from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import bleach
import markdown
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    media_files = db.relationship('MediaFile', backref='uploader', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.username}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_html = db.Column(db.Text)
    summary = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    media_files = db.relationship('MediaFile', backref='post', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        self.generate_html()
    
    def generate_html(self):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                       'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                       'h1', 'h2', 'h3', 'p', 'br', 'img']
        allowed_attrs = {
            '*': ['class'],
            'a': ['href', 'rel'],
            'img': ['src', 'alt', 'width', 'height']
        }
        self.content_html = bleach.linkify(
            bleach.clean(
                markdown.markdown(self.content, output_format='html'),
                tags=allowed_tags,
                attributes=allowed_attrs,
                strip=True
            )
        )
    
    def increment_view_count(self):
        self.view_count += 1
        db.session.commit()
    
    def __repr__(self):
        return f'<Post {self.title}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    content_html = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_approved = db.Column(db.Boolean, default=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False, index=True)
    
    def __init__(self, **kwargs):
        super(Comment, self).__init__(**kwargs)
        self.generate_html()
    
    def generate_html(self):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong', 'br', 'p']
        allowed_attrs = {
            'a': ['href', 'rel']
        }
        self.content_html = bleach.linkify(
            bleach.clean(
                markdown.markdown(self.content, output_format='html'),
                tags=allowed_tags,
                attributes=allowed_attrs,
                strip=True
            )
        )
    
    def __repr__(self):
        return f'<Comment {self.id}>'

class MediaFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # image, video, document
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    s3_key = db.Column(db.String(500))  # S3 object key
    s3_url = db.Column(db.String(500))  # S3 URL
    local_path = db.Column(db.String(500))  # Local file path for development
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True, index=True)
    
    def get_url(self):
        return self.s3_url if self.s3_url else f'/static/uploads/{self.filename}'
    
    def is_image(self):
        return self.file_type == 'image'
    
    def is_video(self):
        return self.file_type == 'video'
    
    def is_document(self):
        return self.file_type == 'document'
    
    def __repr__(self):
        return f'<MediaFile {self.filename}>'

# Database indexes for performance optimization
db.Index('idx_user_email', User.email)
db.Index('idx_user_username', User.username)
db.Index('idx_post_created_at', Post.created_at)
db.Index('idx_post_user_id', Post.user_id)
db.Index('idx_comment_post_id', Comment.post_id)
db.Index('idx_comment_created_at', Comment.created_at)
db.Index('idx_media_user_id', MediaFile.user_id)
db.Index('idx_media_created_at', MediaFile.created_at)