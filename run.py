import os
import logging
from flask.logging import default_handler
from app import create_app, db
from app.models import User, Post, Comment, MediaFile
from flask_migrate import upgrade

# Create Flask application instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell."""
    return {
        'db': db,
        'User': User,
        'Post': Post,
        'Comment': Comment,
        'MediaFile': MediaFile
    }

@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # Migrate database to latest revision
    upgrade()
    
    # Create or update user roles
    from app.models import User
    
    # Create admin user if it doesn't exist
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    admin_user = User.query.filter_by(email=admin_email).first()
    
    if not admin_user:
        admin_user = User(
            username='admin',
            email=admin_email,
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        admin_user.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
        db.session.add(admin_user)
        db.session.commit()
        print(f'Admin user created: {admin_email}')
    else:
        print(f'Admin user already exists: {admin_email}')

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized.')

@app.cli.command()
def create_sample_data():
    """Create sample data for development."""
    from app.models import User, Post
    from datetime import datetime
    import random
    
    # Create sample users
    users_data = [
        {'username': 'john_doe', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'},
        {'username': 'jane_smith', 'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
        {'username': 'bob_wilson', 'email': 'bob@example.com', 'first_name': 'Bob', 'last_name': 'Wilson'},
        {'username': 'alice_brown', 'email': 'alice@example.com', 'first_name': 'Alice', 'last_name': 'Brown'},
    ]
    
    created_users = []
    for user_data in users_data:
        existing_user = User.query.filter_by(email=user_data['email']).first()
        if not existing_user:
            user = User(**user_data)
            user.set_password('password123')
            user.bio = f"Hello! I'm {user_data['first_name']} and I love sharing my thoughts on this platform."
            db.session.add(user)
            created_users.append(user)
    
    db.session.commit()
    
    # Create sample blog posts
    sample_posts = [
        {
            'title': 'Welcome to Our Community Platform',
            'content': '''# Welcome to Our Amazing Community!

We're excited to have you join our growing community of writers, thinkers, and creators. This platform is designed to be a space where you can:

## Share Your Ideas
- Write blog posts about topics you're passionate about
- Upload media to enhance your content
- Engage with other community members

## Connect with Others
- Comment on posts that interest you
- Follow your favorite authors
- Discover new perspectives

## Express Yourself
Our platform supports **Markdown formatting**, so you can create rich, engaging content with ease.

> "The best way to find out if you can trust somebody is to trust them." - Ernest Hemingway

We hope you enjoy your time here and look forward to seeing what you'll share with the community!

Happy writing! 🎉'''
        },
    ]

def hello_world():
    print("Hello, World!")