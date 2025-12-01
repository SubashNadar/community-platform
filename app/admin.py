from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Post, Comment, MediaFile
from app.utils import cache_delete
from datetime import datetime, timedelta
from sqlalchemy import func, desc

bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    total_users = User.query.count()
    total_posts = Post.query.count()
    total_comments = Comment.query.count()
    total_media = MediaFile.query.count()
    
    # Get recent activity
    recent_users = User.query.order_by(desc(User.created_at)).limit(5).all()
    recent_posts = Post.query.order_by(desc(Post.created_at)).limit(5).all()
    recent_comments = Comment.query.order_by(desc(Comment.created_at)).limit(5).all()
    
    # Get growth statistics (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users_30d = User.query.filter(User.created_at >= thirty_days_ago).count()
    new_posts_30d = Post.query.filter(Post.created_at >= thirty_days_ago).count()
    
    # Get storage usage
    total_storage = db.session.query(func.sum(MediaFile.file_size)).scalar() or 0
    total_storage_mb = total_storage / (1024 * 1024)
    
    stats = {
        'total_users': total_users,
        'total_posts': total_posts,
        'total_comments': total_comments,
        'total_media': total_media,
        'new_users_30d': new_users_30d,
        'new_posts_30d': new_posts_30d,
        'total_storage_mb': round(total_storage_mb, 2)
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_users=recent_users,
                         recent_posts=recent_posts,
                         recent_comments=recent_comments)

@bp.route('/users')
@login_required
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(
            User.username.contains(search) | 
            User.email.contains(search) |
            User.first_name.contains(search) |
            User.last_name.contains(search)
        )
    
    users = query.order_by(desc(User.created_at)).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search)

@bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}.', 'success')
    
    return redirect(url_for('admin.manage_users'))

@bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin_status(user_id):
    user = User.query.get_or_404(user_id)
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'granted' if user.is_admin else 'revoked'
    flash(f'Admin privileges {status} for {user.username}.', 'success')
    
    return redirect(url_for('admin.manage_users'))

@bp.route('/posts')
@login_required
@admin_required
def manage_posts():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Post.query
    if search:
        query = query.filter(Post.title.contains(search) | Post.content.contains(search))
    
    posts = query.order_by(desc(Post.created_at)).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    return render_template('admin/posts.html', posts=posts, search=search)

@bp.route('/posts/<int:post_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_post_status(post_id):
    post = Post.query.get_or_404(post_id)
    
    post.is_published = not post.is_published
    db.session.commit()
    
    # Clear cache
    for page in range(1, 6):
        cache_delete(f"feed_page_{page}")
    
    status = 'published' if post.is_published else 'unpublished'
    flash(f'Post "{post.title}" has been {status}.', 'success')
    
    return redirect(url_for('admin.manage_posts'))

@bp.route('/comments')
@login_required
@admin_required
def manage_comments():
    page = request.args.get('page', 1, type=int)
    
    comments = Comment.query.order_by(desc(Comment.created_at)).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    return render_template('admin/comments.html', comments=comments)

@bp.route('/comments/<int:comment_id>/toggle-approval', methods=['POST'])
@login_required
@admin_required
def toggle_comment_approval(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    comment.is_approved = not comment.is_approved
    db.session.commit()
    
    status = 'approved' if comment.is_approved else 'hidden'
    flash(f'Comment has been {status}.', 'success')
    
    return redirect(url_for('admin.manage_comments'))

@bp.route('/media')
@login_required
@admin_required
def manage_media():
    page = request.args.get('page', 1, type=int)
    file_type = request.args.get('type', 'all')
    
    query = MediaFile.query
    if file_type != 'all':
        query = query.filter_by(file_type=file_type)
    
    media_files = query.order_by(desc(MediaFile.created_at)).paginate(
        page=page,
        per_page=20,
        error_out=False
    )
    
    return render_template('admin/media.html', media_files=media_files, current_type=file_type)

@bp.route('/media/<int:media_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_media(media_id):
    media_file = MediaFile.query.get_or_404(media_id)
    
    # TODO: Delete from S3 if exists
    # if media_file.s3_key:
    #     delete_from_s3(media_file.s3_key)
    
    db.session.delete(media_file)
    db.session.commit()
    
    flash('Media file deleted successfully.', 'success')
    return redirect(url_for('admin.manage_media'))

@bp.route('/analytics')
@login_required
@admin_required
def analytics():
    # User growth over last 12 months
    user_growth = []
    for i in range(12):
        date = datetime.utcnow() - timedelta(days=30*i)
        count = User.query.filter(User.created_at <= date).count()
        user_growth.append({
            'month': date.strftime('%Y-%m'),
            'count': count
        })
    user_growth.reverse()
    
    # Post activity over last 30 days
    post_activity = []
    for i in range(30):
        date = datetime.utcnow() - timedelta(days=i)
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        count = Post.query.filter(
            Post.created_at >= start_date,
            Post.created_at < end_date
        ).count()
        post_activity.append({
            'date': start_date.strftime('%Y-%m-%d'),
            'count': count
        })
    post_activity.reverse()
    
    # Top contributors
    top_contributors = db.session.query(
        User.username,
        User.first_name,
        User.last_name,
        func.count(Post.id).label('post_count')
    ).join(Post).group_by(User.id).order_by(desc('post_count')).limit(10).all()
    
    return render_template('admin/analytics.html',
                         user_growth=user_growth,
                         post_activity=post_activity,
                         top_contributors=top_contributors)

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        # Handle settings update
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html')