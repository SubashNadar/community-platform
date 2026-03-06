from app import create_app, db
from app.models import User, Post
from datetime import datetime

app = create_app()

with app.app_context():
    # Get admin user
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        # Create sample posts by admin
        sample_posts = [
            {
                'title': 'Welcome to Our Community Platform',
                'content': '''# Welcome Everyone!

This is our new community platform where you can:

- Share your thoughts and ideas
- Connect with other members
- Upload media files
- Engage in discussions

Feel free to explore and start posting!''',
                'summary': 'Welcome post introducing the community platform features.'
            },
            {
                'title': 'Platform Guidelines and Rules',
                'content': '''# Community Guidelines

Please follow these simple rules:

## Be Respectful
- Treat all members with respect
- No harassment or bullying
- Keep discussions civil

## Content Guidelines
- No spam or promotional content
- Keep posts relevant to the community
- Use appropriate language

## Reporting
If you see any violations, please report them to the admin team.

Thank you for helping us maintain a positive community!''',
                'summary': 'Important guidelines for community members to follow.'
            },
            {
                'title': 'How to Upload Media Files',
                'content': '''# Media Upload Tutorial

You can upload various types of media files:

## Supported Formats
- **Images**: PNG, JPG, JPEG, GIF, WebP
- **Videos**: MP4, AVI, MOV, WMV, FLV  
- **Documents**: PDF, DOC, DOCX, TXT, RTF

## How to Upload
1. Go to the Media Gallery
2. Click "Upload Media"
3. Select your file
4. Add a description (optional)
5. Click "Upload"

## File Limits
- Maximum file size: 100MB
- Files are automatically compressed for images

Happy sharing!''',
                'summary': 'Tutorial on how to upload and manage media files.'
            }
        ]
        
        for post_data in sample_posts:
            # Check if post already exists
            existing_post = Post.query.filter_by(title=post_data['title']).first()
            if not existing_post:
                post = Post(
                    title=post_data['title'],
                    content=post_data['content'],
                    summary=post_data['summary'],
                    user_id=admin.id,
                    is_published=True
                )
                db.session.add(post)
        
        db.session.commit()
        print("Sample posts created successfully!")
    else:
        print("Admin user not found. Please run setup_data.py first.")