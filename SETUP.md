# Community Platform - Complete Setup Guide

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Google Cloud Setup](#google-cloud-setup)
- [Firebase Configuration](#firebase-configuration)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)
- **Google Cloud SDK** - [Download](https://cloud.google.com/sdk/docs/install)

### Required Accounts
- **Google Cloud Account** - [Sign up](https://cloud.google.com/)
- **Firebase Account** - [Sign up](https://firebase.google.com/)

---

## Local Development Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd community-platform
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 5. Create Upload Directory
```bash
mkdir uploads
```

### 6. Setup Initial Data
```bash
python setup_data.py
```

### 7. Run Application

**Development Mode:**
```bash
python debug_run.py
```

**Production Mode:**
```bash
python run.py
```

### 8. Access Application
Open browser: `http://localhost:5000`

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin123`

---

## Google Cloud Setup

### Step 1: Authenticate with Google Cloud
```bash
gcloud auth login
gcloud auth application-default login
```

### Step 2: Run Setup Script

**Windows (PowerShell):**
```bash
bash setup-all-credentials.sh
```

**macOS/Linux:**
```bash
chmod +x setup-all-credentials.sh
./setup-all-credentials.sh
```

This script will:
- ✅ Set up Google Cloud project
- ✅ Enable required APIs
- ✅ Create service account
- ✅ Generate credentials
- ✅ Create Cloud Storage bucket
- ✅ Initialize Firestore database
- ✅ Create `.env` configuration file

### Step 3: Verify Setup
```bash
python verify_setup.py
```

---

## Firebase Configuration

### 1. Access Firebase Console
Go to: https://console.firebase.google.com/

### 2. Add Firebase to Your Project
1. Click **"Add project"**
2. Select your Google Cloud project from dropdown
3. Follow the setup wizard
4. Enable Google Analytics (optional)

### 3. Register Web App
1. Go to **Project Settings** > **General**
2. Scroll down and click **"</> Add app"** (Web)
3. Register app with nickname: `Community Platform Web`
4. Copy the Firebase configuration

### 4. Update .env File
Open `.env` and update these values:
```env
FIREBASE_API_KEY=your_api_key_here
FIREBASE_MESSAGING_SENDER_ID=your_sender_id_here
FIREBASE_APP_ID=your_app_id_here
```

### 5. Enable Authentication
1. Go to **Authentication** > **Sign-in method**
2. Enable **Email/Password**
3. Enable **Google** (optional)

---

## Deployment

### Deploy to Cloud Run

**Option 1: Using gcloud CLI**
```bash
gcloud run deploy community-platform-web \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 100 \
  --min-instances 1
```

**Option 2: Using Cloud Build**
```bash
gcloud builds submit --config cloudbuild.yaml
```

### Access Deployed Application
After deployment, you'll receive a URL like:
```
https://community-platform-web-xxxxx-uc.a.run.app
```

---

## Project Structure

```
community-platform/
├── app/                    # Application package
│   ├── templates/         # HTML templates
│   ├── __init__.py       # App initialization
│   ├── admin.py          # Admin routes
│   ├── auth.py           # Authentication
│   ├── main.py           # Main routes
│   ├── models.py         # Database models
│   └── utils.py          # Utility functions
├── static/                # Static files (CSS, JS)
├── uploads/               # Local file uploads
├── credentials/           # GCP credentials (gitignored)
├── migrations/            # Database migrations
├── .env                   # Environment variables (gitignored)
├── app.py                 # Application entry point
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
├── setup_data.py          # Initial data setup
├── debug_run.py           # Development server
├── run.py                 # Production server
├── Dockerfile             # Docker configuration
├── cloudbuild.yaml        # Cloud Build config
└── setup-all-credentials.sh  # GCP setup script
```

---

## Environment Variables

### Core Settings
```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json
ENVIRONMENT=production
```

### Database
```env
USE_FIRESTORE=true
FIRESTORE_DATABASE=(default)
```

### Storage
```env
USE_CLOUD_STORAGE=true
GCS_PRIMARY_BUCKET=your-bucket-name
GCS_REGION=us-central1
```

### Firebase
```env
USE_FIREBASE_AUTH=true
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
```

---

## Troubleshooting

### Database Issues
```bash
flask db stamp head
flask db migrate
flask db upgrade
```

### Permission Issues (Linux/macOS)
```bash
chmod +x venv/bin/activate
chmod +x setup-all-credentials.sh
```

### Port Already in Use
```bash
python debug_run.py --port 5001
```

### Reset Database
```bash
python setup_data.py
```

### Google Cloud Authentication Issues
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### Verify Credentials
```bash
python verify_credentials.py
```

### Check Service Account Permissions
```bash
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*"
```

---

## Useful Commands

### Google Cloud
```bash
# List projects
gcloud projects list

# Set active project
gcloud config set project PROJECT_ID

# List storage buckets
gsutil ls

# View Firestore data
gcloud firestore databases list

# View Cloud Run services
gcloud run services list
```

### Flask
```bash
# Create new migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

### Python
```bash
# Install new package
pip install package-name
pip freeze > requirements.txt

# Update all packages
pip install --upgrade -r requirements.txt
```

---

## Security Best Practices

1. **Never commit credentials**
   - `.env` file is gitignored
   - `credentials/` folder is gitignored
   - Service account keys are gitignored

2. **Use environment variables**
   - All sensitive data in `.env`
   - Different configs for dev/prod

3. **Secure your service account**
   - Limit permissions to minimum required
   - Rotate keys regularly
   - Monitor usage in Cloud Console

4. **Enable security features**
   - Cloud Armor for DDoS protection
   - Identity-Aware Proxy for access control
   - Cloud Monitoring for alerts

---

## Support & Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Google Cloud Documentation](https://cloud.google.com/docs)
- [Firebase Documentation](https://firebase.google.com/docs)

### Console Links
- [Google Cloud Console](https://console.cloud.google.com/)
- [Firebase Console](https://console.firebase.google.com/)
- [Cloud Storage Browser](https://console.cloud.google.com/storage/browser)
- [Firestore Data](https://console.cloud.google.com/firestore/data)
- [Cloud Run Services](https://console.cloud.google.com/run)

---

## License

[Your License Here]

## Contributors

[Your Name/Team Here]
