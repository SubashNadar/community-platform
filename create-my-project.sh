#!/bin/bash

echo "🚀 Creating YOUR OWN Community Platform Project"
echo "=============================================="

# Generate unique project ID (must be globally unique)
RANDOM_ID=$(echo $RANDOM | md5sum | head -c 6)
PROJECT_ID="community-platform-${RANDOM_ID}"

echo "Creating new project: $PROJECT_ID"
echo "You will be the OWNER of this project"
echo ""

# Create the project (you'll be owner automatically)
gcloud projects create $PROJECT_ID \
    --name="My Community Platform" \
    --set-as-default

if [ $? -eq 0 ]; then
    echo "✅ Project created successfully!"
    echo "Project ID: $PROJECT_ID"
    
    # Set as active project
    gcloud config set project $PROJECT_ID
    
    echo ""
    echo "You are now the OWNER of: $PROJECT_ID"
    echo ""
    
    # Save project ID for later use
    echo $PROJECT_ID > .project-id
    
    echo "Next step: Enable billing (required for most services)"
    echo "Visit: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
    
else
    echo "❌ Project creation failed. Try a different ID:"
    echo ""
    echo "Run: gcloud projects create community-platform-YOUR_UNIQUE_ID"
fi