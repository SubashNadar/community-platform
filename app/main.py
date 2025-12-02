import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Post, Comment, MediaFile
from app.utils import (allowed_file, get_file_type, generate_unique_filename, 
                      compress_image, upload_to_s3, validate_file_content, 
                      get_file_size_mb, cache_get, cache_set, cache_delete)
from datetime import datetime
from sqlalchemy import desc

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    
    # Try to get from cache first
    cache_key = f"feed_page_{page}"
    cached_posts = cache_get(cache_key)
    
    if cached_posts:
        posts = cached_posts
    else:
        # Get posts with pagination
        posts_query = Post.query.filter_by(is_published=True).order_by(desc(Post.created_at))
        posts_pagination = posts_query.paginate(
            page=page, 
            per_page=current_app.config['POSTS_PER_PAGE'],
            error_out=False
        )
        
        posts = {
            'items': [
                {
                    'id': post.id,
                    'title': post.title,
                    'content_html': post.content_html,
                    'summary': post.summary,
                    'author': post.author.get_full_name(),
                    'author_username': post.author.username,
                    'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
                    'view_count': post.view_count,
                    'comment_count': post.comments.count()
                } for post in posts_pagination.items
            ],
            'has_next': posts_pagination.has_next,
            'has_prev': posts_pagination.has_prev,
            'next_num': posts_pagination.next_num,
            'prev_num': posts_pagination.prev_num,
            'page': page,
            'pages': posts_pagination.pages
        }
        
        # Cache for 5 minutes
        cache_set(cache_key, posts, 300)
    
    # Get recent media files
    recent_media = MediaFile.query.order_by(desc(MediaFile.created_at)).limit(6).all()
    
    return render_template('index.html', posts=posts, recent_media=recent_media)

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_media():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        description = request.form.get('description', '')
        
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = generate_unique_filename(file.filename)
            
            # Create upload directory if it doesn't exist
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file temporarily
            temp_path = os.path.join(upload_dir, filename)
            file.save(temp_path)
            
            # Validate file content
            is_valid, mime_type = validate_file_content(temp_path)
            if not is_valid:
                os.remove(temp_path)
                flash('Invalid file type.', 'error')
                return redirect(request.url)
            
            # Check file size (max 100MB)
            file_size_mb = get_file_size_mb(temp_path)
            if file_size_mb > 100:
                os.remove(temp_path)
                flash('File size too large. Maximum 100MB allowed.', 'error')
                return redirect(request.url)
            
            file_type = get_file_type(filename)
            
            # Compress image if it's an image
            if file_type == 'image':
                compress_image(temp_path)
            
            # Upload to S3 if configured
            s3_key = None
            s3_url = None
            if current_app.config.get('AWS_S3_BUCKET'):
                s3_key, s3_url = upload_to_s3(
                    temp_path, 
                    filename, 
                    current_app.config['AWS_S3_BUCKET']
                )
                
                # Remove local file if S3 upload successful
                if s3_url:
                    os.remove(temp_path)
                    temp_path = None
            
            # Create media file record
            media_file = MediaFile(
                filename=filename,
                original_filename=secure_filename(file.filename),
                file_type=file_type,
                file_size=int(file_size_mb * 1024 * 1024),
                mime_type=mime_type,
                s3_key=s3_key,
                s3_url=s3_url,
                local_path=temp_path,
                description=description,
                user_id=current_user.id
            )
            
            db.session.add(media_file)
            db.session.commit()
            
            # Clear cache
            cache_delete('recent_media')
            
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('main.media_gallery'))
        else:
            flash('Invalid file type.', 'error')
    
    return render_template('upload.html')

@bp.route('/media')
def media_gallery():
    page = request.args.get('page', 1, type=int)
    file_type = request.args.get('type', 'all')
    
    query = MediaFile.query
    
    if file_type != 'all':
        query = query.filter_by(file_type=file_type)
    
    media_files = query.order_by(desc(MediaFile.created_at)).paginate(
        page=page,
        per_page=12,
        error_out=False
    )
    
    return render_template('media_gallery.html', media_files=media_files, current_type=file_type)

@bp.route('/blog/create', methods=['GET', 'POST'])
@login_required
def create_blog():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        summary = request.form.get('summary')
        
        if not title or not content:
            flash('Title and content are required.', 'error')
            return render_template('blog_create.html')
        
        # Create new post
        post = Post(
            title=title,
            content=content,
            summary=summary or content[:200] + '...' if len(content) > 200 else content,
            user_id=current_user.id
        )
        
        db.session.add(post)
        db.session.commit()
        
        # Clear cache
        for page in range(1, 6):  # Clear first 5 pages of cache
            cache_delete(f"feed_page_{page}")
        
        flash('Blog post created successfully!', 'success')
        return redirect(url_for('main.blog_detail', id=post.id))
    
    return render_template('blog_create.html')

@bp.route('/blog/<int:id>')
def blog_detail(id):
    post = Post.query.get_or_404(id)
    
    # Increment view count
    post.increment_view_count()
    
    # Get comments with pagination
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.filter_by(post_id=id, is_approved=True)\
                           .order_by(desc(Comment.created_at))\
                           .paginate(
                               page=page,
                               per_page=current_app.config['COMMENTS_PER_PAGE'],
                               error_out=False)
    
    # Get related posts by the same author
    related_posts = Post.query.filter_by(user_id=post.user_id, is_published=True)\
                             .filter(Post.id != post.id)\
                             .order_by(desc(Post.created_at))\
                             .limit(3).all()
    
    return render_template('blog_detail.html', post=post, comments=comments, related_posts=related_posts)


@bp.route('/blog/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    post = Post.query.get_or_404(id)
    content = request.form.get('content')
    
    if not content:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('main.blog_detail', id=id))
    
    comment = Comment(
        content=content,
        user_id=current_user.id,
        post_id=id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    flash('Comment added successfully!', 'success')
    return redirect(url_for('main.blog_detail', id=id))

@bp.route('/blog/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_blog(id):
    post = Post.query.get_or_404(id)
    
    # Check if user owns the post or is admin
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('You can only edit your own posts.', 'error')
        return redirect(url_for('main.blog_detail', id=id))
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.summary = request.form.get('summary')
        post.updated_at = datetime.utcnow()
        post.generate_html()
        
        db.session.commit()
        
        # Clear cache
        for page in range(1, 6):
            cache_delete(f"feed_page_{page}")
        
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('main.blog_detail', id=id))
    
    return render_template('blog_create.html', post=post, edit_mode=True)

@bp.route('/blog/<int:id>/delete', methods=['POST'])
@login_required
def delete_blog(id):
    post = Post.query.get_or_404(id)
    
    # Check if user owns the post or is admin
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('You can only delete your own posts.', 'error')
        return redirect(url_for('main.blog_detail', id=id))
    
    db.session.delete(post)
    db.session.commit()
    
    # Clear cache
    for page in range(1, 6):
        cache_delete(f"feed_page_{page}")
    
    flash('Blog post deleted successfully!', 'success')
    return redirect(url_for('main.index'))

@bp.route('/user/<username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    # Get user's posts
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(user_id=user.id, is_published=True)\
                     .order_by(desc(Post.created_at))\
                     .paginate(
                         page=page,
                         per_page=current_app.config['POSTS_PER_PAGE'],
                         error_out=False
                     )
    
    # Get user's recent media
    recent_media = MediaFile.query.filter_by(user_id=user.id)\
                                 .order_by(desc(MediaFile.created_at))\
                                 .limit(6).all()
    
    return render_template('user_profile.html', user=user, posts=posts, recent_media=recent_media)

@bp.route('/search')
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return render_template('search_results.html', posts=None, media_files=None, query='')
    
    # Search posts
    posts = Post.query.filter(
        Post.title.contains(query) | Post.content.contains(query),
        Post.is_published == True
    ).order_by(desc(Post.created_at)).paginate(
        page=page,
        per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    
    # Search media files
    media_files = MediaFile.query.filter(
        MediaFile.description.contains(query) | MediaFile.original_filename.contains(query)
    ).order_by(desc(MediaFile.created_at)).limit(10).all()
    
    return render_template('search_results.html', posts=posts, media_files=media_files, query=query)

@bp.route('/api/posts')
def api_posts():
    """API endpoint for posts - useful for AJAX loading"""
    page = request.args.get('page', 1, type=int)
    
    posts = Post.query.filter_by(is_published=True)\
                     .order_by(desc(Post.created_at))\
                     .paginate(
                         page=page,
                         per_page=current_app.config['POSTS_PER_PAGE'],
                         error_out=False
                     )
    
    return jsonify({
        'posts': [
            {
                'id': post.id,
                'title': post.title,
                'content_html': post.content_html,
                'author': post.author.get_full_name(),
                'created_at': post.created_at.isoformat(),
                'view_count': post.view_count
            } for post in posts.items
        ],
        'has_next': posts.has_next,
        'has_prev': posts.has_prev,
        'page': page,
        'pages': posts.pages
    })

@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files in development"""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
