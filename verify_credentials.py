#!/usr/bin/env python3
"""
Script to verify all credentials are properly set
"""
import os
import json
from pathlib import Path

def check_credentials():
    print("🔍 Checking credentials setup...\n")
    
    issues = []
    
    # Check .env file
    if not Path('.env').exists():
        issues.append("❌ .env file not found")
    else:
        print("✅ .env file exists")
        
        # Load .env and check values
        with open('.env', 'r') as f:
            env_content = f.read()
            
        required_vars = [
            'GOOGLE_CLOUD_PROJECT',
            'GOOGLE_APPLICATION_CREDENTIALS',
            'FIREBASE_API_KEY',
            'GCS_PRIMARY_BUCKET'
        ]
        
        for var in required_vars:
            if var not in env_content:
                issues.append(f"❌ {var} not found in .env")
            elif 'PENDING_UPDATE' in env_content or 'YOUR_' in env_content:
                issues.append(f"⚠️  {var} needs to be updated with actual value")
    
    # Check service account file
    sa_path = './credentials/service-account.json'
    if not Path(sa_path).exists():
        issues.append("❌ Service account JSON not found at " + sa_path)
    else:
        print("✅ Service account JSON exists")
        
        # Verify it's valid JSON
        try:
            with open(sa_path, 'r') as f:
                sa_data = json.load(f)
                if 'project_id' in sa_data:
                    print(f"   Project ID: {sa_data['project_id']}")
                if 'client_email' in sa_data:
                    print(f"   Service Account: {sa_data['client_email']}")
        except json.JSONDecodeError:
            issues.append("❌ Service account JSON is invalid")
    
    # Check .gitignore
    if Path('.gitignore').exists():
        with open('.gitignore', 'r') as f:
            gitignore = f.read()
            if 'credentials/' in gitignore and '.env' in gitignore:
                print("✅ Security: credentials are in .gitignore")
            else:
                issues.append("⚠️  Add credentials/ and .env to .gitignore!")
    else:
        issues.append("⚠️  Create .gitignore file for security")
    
    # Summary
    print("\n" + "="*50)
    if issues:
        print("❌ Issues found:\n")
        for issue in issues:
            print(f"   {issue}")
        print("\n💡 Run: bash setup-all-credentials.sh")
    else:
        print("✅ All credentials are properly configured!")
        print("\n🚀 Ready to deploy: gcloud run deploy")
    
    return len(issues) == 0

if __name__ == "__main__":
    check_credentials()