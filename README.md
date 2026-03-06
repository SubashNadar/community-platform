# Community Platform

A modern web-based community platform built with Flask, featuring user management, content creation, media uploads, and administrative controls — backed by Google Cloud (Firestore, Cloud Storage, Firebase Auth, Cloud Run).

---

## Prerequisites

- Python 3.8+
- Git
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- A Google Cloud account with billing enabled

---

## Quick Start (Local Development)

### 1. Clone & Enter Repo
```bash
git clone <repository-url>
cd community-platform
```

### 2. Create & Activate Virtual Environment

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
flask db upgrade
```

### 5. Create Upload Directory
```bash
mkdir uploads
```

### 6. Setup Initial Data & Admin User
```bash
python setup_data.py
```

### 7. Run Application

**Development:**
```bash
python debug_run.py
```

**Production:**
```bash
python run.py
```

### 8. Open in Browser
```
http://localhost:5000
```

**Default Admin Login:**
- Username: `admin`
- Password: `admin123`

---

## Google Cloud Setup (Required for Production)

### Step 1: Authenticate with Google Cloud
```bash
gcloud auth login
gcloud auth application-default login
```

### Step 2: Run the Automated Setup Script

This script sets up everything — service account, APIs, Firestore, Cloud Storage, and generates your `.env` file.

**macOS/Linux:**
```bash
chmod +x setup-all-credentials.sh
./setup-all-credentials.sh
```

**Windows (Git Bash or WSL):**
```bash
bash setup-all-credentials.sh
```

The script will:
- ✅ Enable required GCP APIs
- ✅ Create a service account with correct permissions
- ✅ Generate `credentials/service-account.json`
- ✅ Create a Cloud Storage bucket
- ✅ Initialize Firestore database
- ✅ Create your `.env` configuration file

### Step 3: Configure Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **Add project** → select your GCP project from the dropdown
3. Go to **Project Settings** → **General** → scroll down → click **`</> Add app`** (Web)
4. Register with nickname: `Community Platform Web`
5. Copy the config values and update your `.env`:

```env
FIREBASE_API_KEY=your_api_key
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
```

6. In Firebase Console → **Authentication** → **Sign-in method** → enable **Email/Password**

### Step 4: Verify Setup
```bash
python verify_setup.py
```

---

## Deploy to Cloud Run

```bash
gcloud run deploy community-platform-web \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

Or using Cloud Build:
```bash
gcloud builds submit --config cloudbuild.yaml
```

---

## Project Structure

```
community-platform/
├── app/                    # Flask application package
│   ├── templates/         # HTML templates
│   ├── __init__.py
│   ├── admin.py
│   ├── auth.py
│   ├── main.py
│   ├── models.py
│   └── utils.py
├── migrations/             # Database migrations (Alembic)
├── static/                 # CSS, JS assets
├── uploads/                # Local file uploads (gitignored)
├── credentials/            # GCP credentials (gitignored)
├── .env                    # Environment variables (gitignored)
├── app.py                  # App entry point
├── config.py               # App configuration
├── requirements.txt        # Python dependencies
├── setup_data.py           # Seeds initial admin data
├── setup-all-credentials.sh  # Automated GCP setup
├── verify_setup.py         # Verifies GCP/Firebase config
├── storage_manager.py      # Cloud Storage handler
├── Dockerfile              # Container config
└── cloudbuild.yaml         # Cloud Build deployment config
```

---

## Environment Variables

After running `setup-all-credentials.sh`, your `.env` is auto-generated. Key variables:

| Variable | Description |
|---|---|
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON |
| `GCS_PRIMARY_BUCKET` | Cloud Storage bucket name |
| `FIREBASE_API_KEY` | Firebase web API key (manual) |
| `FIREBASE_APP_ID` | Firebase app ID (manual) |
| `FIREBASE_MESSAGING_SENDER_ID` | Firebase sender ID (manual) |

---

## Troubleshooting

**Database issues:**
```bash
flask db stamp head && flask db migrate && flask db upgrade
```

**Port already in use:**
```bash
python debug_run.py --port 5001
```

**GCP auth issues:**
```bash
gcloud auth login
gcloud auth application-default login
```

**Verify credentials:**
```bash
python verify_credentials.py
```

**Reset data:**
```bash
python setup_data.py
```

---

## Useful Links

- [Google Cloud Console](https://console.cloud.google.com/)
- [Firebase Console](https://console.firebase.google.com/)
- [Cloud Run Services](https://console.cloud.google.com/run)
- [Cloud Storage Browser](https://console.cloud.google.com/storage/browser)
- [Firestore Data](https://console.cloud.google.com/firestore/data)
