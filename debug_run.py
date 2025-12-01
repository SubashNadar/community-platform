#!/usr/bin/env python3
import os
import sys

try:
    print("Starting application...")
    from app import create_app, db
    print("Imports successful")
    
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    print("App created successfully")
    
    @app.shell_context_processor
    def make_shell_context():
        from app.models import User, Post, Comment, MediaFile
        return {
            'db': db,
            'User': User,
            'Post': Post,
            'Comment': Comment,
            'MediaFile': MediaFile
        }
    
    print("Starting Flask development server...")
    app.run(debug=True, host='127.0.0.1', port=5000)
    
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)