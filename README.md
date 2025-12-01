# Community Platform

A modern web-based community platform built with Flask, featuring user management, content creation, media uploads, and administrative controls.

## Quick Setup & Run

### Prerequisites

- Python 3.8+
- Git

### Setup Commands

1. **Clone Repository**

```bash
git clone <repository-url>
```

```bash
cd community-platform
```

2. **Create Virtual Environment**

```bash
python -m venv venv
```

3. **Activate Virtual Environment**

**Windows:**

```bash
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

4. **Install Dependencies**

```bash
pip install -r requirements.txt
```

5. **Environment Configuration**

```bash
copy .env.example .env
```

Or create `.env` manually:

```bash
echo "FLASK_APP=app.py" > .env
```

```bash
echo "FLASK_ENV=development" >> .env
```

```bash
echo "SECRET_KEY=your-secret-key-here" >> .env
```

6. **Database Setup**

```bash
flask db init
```

```bash
flask db migrate -m "Initial migration"
```

```bash
flask db upgrade
```

7. **Create Upload Directory**

```bash
mkdir uploads
```

8. **Setup Initial Data**

```bash
python setup_data.py
```

9. **Run Application (Debug Mode)**

```bash
python debug_run.py
```

10. **Run Application (Production Mode)**

```bash
python run.py
```

11. **Access Application**

Open browser: `http://localhost:5000`

### Default Admin Login

After running `setup_data.py`, use these credentials:

- Username: `admin`
- Password: `admin123`

## Features

- User registration and authentication
- Post creation with Markdown support
- Media file uploads
- Comment system with moderation
- Admin panel for user and content management
- Progressive Web App capabilities

## Development vs Production

**For Development (with debug features):**

```bash
python debug_run.py
```

**For Production (optimized):**

```bash
python run.py
```

## Troubleshooting

**Database issues:**

```bash
flask db stamp head
```

```bash
flask db migrate
```

```bash
flask db upgrade
```

**Permission issues (Linux/macOS):**

```bash
chmod +x venv/bin/activate
```

**Port already in use:**

```bash
python debug_run.py --port 5001
```

**Reset database and data:**

```bash
python setup_data.py
```

That's it! Your community platform is ready to use.
