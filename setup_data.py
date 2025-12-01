from run import app
from app import db
from app.models import User, Post

app.app_context().push()

# Check if admin user already exists
admin = User.query.filter_by(username='admin').first()
if not admin:
    admin = User(
        username='admin',
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        is_admin=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print('Admin user created!')
else:
    print('Admin user already exists')

# Create sample users only if they don't exist
users_data = [
    {'username': 'john_doe', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'},
    {'username': 'jane_smith', 'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith'}
]

for user_data in users_data:
    existing_user = User.query.filter_by(username=user_data['username']).first()
    if not existing_user:
        user = User(**user_data)
        user.set_password('password123')
        user.bio = f"Hello! I am {user_data['first_name']} and I love this community!"
        db.session.add(user)
        print(f"Created user: {user_data['username']}")
    else:
        print(f"User {user_data['username']} already exists")

db.session.commit()

# Create sample posts only if they don't exist
posts_data = [
    {
        'title': 'Welcome to Our Community Platform',
        'content': '''# Welcome to Our Amazing Community!

We are excited to have you join our growing community of writers, thinkers, and creators. This platform is designed to be a space where you can:

## Share Your Ideas
- Write blog posts about topics you are passionate about
- Upload media to enhance your content
- Engage with other community members

## Connect with Others
- Comment on posts that interest you
- Follow your favorite authors
- Discover new perspectives

Happy writing! 🎉'''
    },
    {
        'title': 'Getting Started with Markdown',
        'content': '''# Mastering Markdown for Better Blog Posts

Markdown is a lightweight markup language that makes it easy to format your text. Here are some basics:

## Basic Formatting

**Bold text** is created with double asterisks
*Italic text* uses single asterisks

## Lists

- First item
- Second item
- Third item

## Links

[This is a link](https://example.com)

Happy formatting! 📝'''
    },
    {
        'title': 'Community Guidelines',
        'content': '''# Community Guidelines

Welcome to our community! Please follow these guidelines:

## Be Respectful
- Treat all members with kindness
- No harassment or hate speech
- Respect different opinions

## Share Quality Content
- Post relevant content
- Use clear titles
- Credit sources

## Engage Positively
- Leave constructive comments
- Help newcomers
- Report issues to moderators

Thank you! 🌟'''
    }
]

users = User.query.all()
if users:
    for i, post_data in enumerate(posts_data):
        existing_post = Post.query.filter_by(title=post_data['title']).first()
        if not existing_post:
            user = users[i % len(users)]
            post = Post(
                title=post_data['title'],
                content=post_data['content'],
                user_id=user.id,
                is_published=True
            )
            db.session.add(post)
            print(f"Created post: {post_data['title']}")
        else:
            print(f"Post '{post_data['title']}' already exists")

db.session.commit()

print('\n=== Setup Complete ===')
print(f'Total users: {User.query.count()}')
print(f'Total posts: {Post.query.count()}')
print('\nLogin credentials:')
print('Admin - Username: admin, Password: admin123')
print('User 1 - Username: john_doe, Password: password123')
print('User 2 - Username: jane_smith, Password: password123')
