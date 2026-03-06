#!/usr/bin/env python3
import os
import json
from pathlib import Path

def verify_setup():
    print("🔍 Verifying Community Platform Setup")
    print("=" * 40)
    
    project_id = "community-platform-481813"
    issues = []
    
    # Check .env
    if Path('.env').exists():
        print("✅ .env file exists")
    else:
        issues.append("❌ .env file missing")
    
    # Check service account
    sa_path = './credentials/service-account.json'
    if Path(sa_path).exists():
        with open(sa_path) as f:
            sa = json.load(f)
            if sa.get('project_id') == project_id:
                print(f"✅ Service account configured for {project_id}")
            else:
                issues.append(f"❌ Service account project mismatch")
    else:
        issues.append("❌ Service account JSON missing")
    
    # Check .gitignore
    if Path('.gitignore').exists():
        print("✅ .gitignore exists")
    else:
        issues.append("⚠️  .gitignore missing - security risk!")
    
    if issues:
        print("\n❌ Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ All checks passed! Ready to deploy.")
        print(f"\nProject URL: https://console.cloud.google.com/home/dashboard?project={project_id}")

if __name__ == "__main__":
    verify_setup()