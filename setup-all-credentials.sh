#!/bin/bash

echo "🚀 Setting up Community Platform"
echo "================================"
echo "Project ID: community-platform-bd3953"
echo "Project Number: 1095556286348"
echo ""

# Step 1: Set the project
PROJECT_ID="community-platform-bd3953"
gcloud config set project $PROJECT_ID

echo "✅ Project set to: $PROJECT_ID"

# Step 2: Verify authentication
ACCOUNT=$(gcloud config get-value account)
echo "✅ Authenticated as: $ACCOUNT"

# Step 3: Enable required APIs
echo -e "\n📡 Enabling required APIs (this may take 2-3 minutes)..."

gcloud services enable \
    cloudresourcemanager.googleapis.com \
    serviceusage.googleapis.com \
    iam.googleapis.com \
    storage-api.googleapis.com \
    storage-component.googleapis.com \
    firestore.googleapis.com \
    firebase.googleapis.com \
    firebaseauth.googleapis.com \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    --project=$PROJECT_ID

echo "✅ APIs enabled!"

# Step 4: Create credentials directory
mkdir -p credentials

# Step 5: Create service account
echo -e "\n👤 Creating service account..."
SA_NAME="community-platform-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account exists
if gcloud iam service-accounts describe $SA_EMAIL --project=$PROJECT_ID &>/dev/null; then
    echo "Service account already exists"
else
    gcloud iam service-accounts create $SA_NAME \
        --display-name="Community Platform Service Account" \
        --project=$PROJECT_ID
    echo "✅ Service account created!"
fi

# Step 6: Grant permissions
echo -e "\n🔐 Granting permissions to service account..."

for role in editor storage.admin datastore.user firebase.admin; do
    echo "Granting $role..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/$role" \
        --quiet \
        --project=$PROJECT_ID
done

echo "✅ Permissions granted!"

# Step 7: Create service account key
echo -e "\n📥 Creating service account key..."

if [ -f "./credentials/service-account.json" ]; then
    echo "Service account key already exists. Skipping..."
else
    gcloud iam service-accounts keys create \
        ./credentials/service-account.json \
        --iam-account=$SA_EMAIL \
        --project=$PROJECT_ID
    echo "✅ Service account key created!"
fi

# Step 8: Create storage bucket
echo -e "\n🪣 Creating storage bucket..."
BUCKET_NAME="${PROJECT_ID}-media-001"

# Check if bucket exists
if gsutil ls -b gs://$BUCKET_NAME &>/dev/null; then
    echo "Bucket gs://$BUCKET_NAME already exists"
else
    # Create bucket
    gsutil mb -p $PROJECT_ID -c STANDARD -l us-central1 gs://$BUCKET_NAME/
    
    # Make bucket public for read access
    gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
    
    echo "✅ Bucket created: gs://$BUCKET_NAME"
fi

# Step 9: Initialize Firestore
echo -e "\n🔥 Initializing Firestore..."

# Check if App Engine is initialized (required for Firestore)
if ! gcloud app describe --project=$PROJECT_ID &>/dev/null; then
    echo "Creating App Engine app (required for Firestore)..."
    gcloud app create --region=us-central --project=$PROJECT_ID
fi

# Create Firestore database
if ! gcloud firestore databases describe --project=$PROJECT_ID &>/dev/null; then
    gcloud firestore databases create \
        --location=us-central1 \
        --type=firestore-native \
        --project=$PROJECT_ID
    echo "✅ Firestore initialized!"
else
    echo "Firestore already initialized"
fi

# Step 10: Create .env file
echo -e "\n📝 Creating .env file..."

cat > .env << EOF
# ============================================
# GOOGLE CLOUD CONFIGURATION
# ============================================

# Core Settings
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account.json
ENVIRONMENT=production

# ============================================
# FIRESTORE DATABASE
# ============================================
USE_FIRESTORE=true
FIRESTORE_DATABASE=(default)

# ============================================
# GOOGLE CLOUD STORAGE
# ============================================
USE_CLOUD_STORAGE=true
GCS_PRIMARY_BUCKET=$BUCKET_NAME
GCS_BUCKET_PREFIX=${PROJECT_ID}-media-
GCS_REGION=us-central1
GCS_STORAGE_CLASS=STANDARD

# Auto-scaling Storage Configuration
STORAGE_AUTO_EXTEND=true
INITIAL_BUCKET_SIZE_GB=100
MAX_BUCKET_SIZE_GB=1000
MAX_BUCKETS=100
STORAGE_WARNING_THRESHOLD=80
STORAGE_CRITICAL_THRESHOLD=95
CURRENT_BUCKET_INDEX=1

# ============================================
# FIREBASE CONFIGURATION (UPDATE THESE!)
# ============================================
USE_FIREBASE_AUTH=true
FIREBASE_API_KEY=YOUR_FIREBASE_API_KEY_HERE
FIREBASE_AUTH_DOMAIN=${PROJECT_ID}.firebaseapp.com
FIREBASE_PROJECT_ID=$PROJECT_ID
FIREBASE_STORAGE_BUCKET=${PROJECT_ID}.appspot.com
FIREBASE_MESSAGING_SENDER_ID=YOUR_SENDER_ID_HERE
FIREBASE_APP_ID=YOUR_APP_ID_HERE

# ============================================
# CLOUD RUN DEPLOYMENT
# ============================================
CLOUD_RUN_SERVICE=community-platform-web
CLOUD_RUN_REGION=us-central1
CLOUD_RUN_MEMORY=2Gi
CLOUD_RUN_CPU=2
CLOUD_RUN_MAX_INSTANCES=100
CLOUD_RUN_MIN_INSTANCES=1

# ============================================
# MONITORING & ALERTS
# ============================================
ENABLE_CLOUD_MONITORING=true
ENABLE_CLOUD_LOGGING=true
ALERT_EMAIL=$ACCOUNT

# ============================================
# APPLICATION SETTINGS
# ============================================
MAX_FILE_SIZE_MB=100
ALLOWED_FILE_TYPES=jpg,jpeg,png,gif,mp4,pdf,doc,docx
MAX_POST_LENGTH=5000
RATE_LIMIT_PER_MINUTE=60
EOF

echo "✅ .env file created!"

# Step 11: Create .gitignore
echo -e "\n🔒 Creating .gitignore..."

cat > .gitignore << EOF
# Credentials - NEVER COMMIT THESE
credentials/
*.json
.env
.env.*
service-account.json
firebase-admin-sdk.json

# Python
__pycache__/
*.py[cod]
*\$py.class
*.so
.Python
env/
venv/
.venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF

echo "✅ .gitignore created!"

# Step 12: Create requirements.txt
echo -e "\n📦 Creating requirements.txt..."

cat > requirements.txt << EOF
# Google Cloud
google-cloud-firestore==2.11.1
google-cloud-storage==2.10.0
google-cloud-logging==3.5.0

# Firebase
firebase-admin==6.1.0

# Web Framework
Flask==2.3.2
gunicorn==20.1.0

# Utilities
python-dotenv==1.0.0
Pillow==10.0.0
EOF

echo "✅ requirements.txt created!"

# Final instructions
echo ""
echo "========================================="
echo "✅ PROJECT SETUP COMPLETE!"
echo "========================================="
echo ""
echo "Project Details:"
echo "  Project ID: $PROJECT_ID"
echo "  Project Number: 1095556286348"
echo "  Console: https://console.cloud.google.com/home/dashboard?project=$PROJECT_ID"
echo "  Storage Bucket: gs://$BUCKET_NAME"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. SET UP FIREBASE:"
echo "   a. Go to: https://console.firebase.google.com/"
echo "   b. Click 'Add project'"
echo "   c. Select 'community-platform-481813' from the dropdown"
echo "   d. Follow the setup wizard"
echo "   e. Go to Project Settings > General"
echo "   f. Scroll down and click '</> Add app' (Web)"
echo "   g. Register app with nickname 'Community Platform Web'"
echo "   h. Copy the configuration and update these in .env:"
echo "      - FIREBASE_API_KEY"
echo "      - FIREBASE_MESSAGING_SENDER_ID"
echo "      - FIREBASE_APP_ID"
echo ""
echo "2. VERIFY SETUP:"
echo "   python3 verify_setup.py"
echo ""
echo "3. DEPLOY YOUR APP:"
echo "   gcloud run deploy community-platform-web \\"
echo "     --source . \\"
echo "     --region us-central1 \\"
echo "     --allow-unauthenticated \\"
echo "     --project=$PROJECT_ID"
echo ""
echo "Files Created:"
echo "  ✅ ./credentials/service-account.json"
echo "  ✅ ./.env"
echo "  ✅ ./.gitignore"
echo "  ✅ ./requirements.txt"
echo ""
echo "Direct Links:"
echo "  Firebase: https://console.firebase.google.com/project/$PROJECT_ID"
echo "  Cloud Storage: https://console.cloud.google.com/storage/browser?project=$PROJECT_ID"
echo "  Firestore: https://console.cloud.google.com/firestore/data?project=$PROJECT_ID"
