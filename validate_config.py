#!/usr/bin/env python3
"""
Configuration validation script for billing-backend
This script validates the configuration files without requiring Django to be installed
"""

import os
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and report status"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT FOUND")
        return False

def check_dockerfile():
    """Validate Dockerfile syntax and content"""
    dockerfile_path = "Dockerfile"
    if not os.path.exists(dockerfile_path):
        print("❌ Dockerfile not found")
        return False
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check for required sections
    if "FROM python:3.13-slim" not in content:
        issues.append("Missing Python base image")
    
    if "WORKDIR /app" not in content:
        issues.append("Missing WORKDIR")
    
    if "EXPOSE 8000" not in content:
        issues.append("Missing EXPOSE directive")
    
    if "python manage.py collectstatic" not in content:
        issues.append("Missing static file collection")
    
    if "CMD" not in content:
        issues.append("Missing CMD directive")
    
    if issues:
        print(f"❌ Dockerfile issues: {', '.join(issues)}")
        return False
    else:
        print("✅ Dockerfile looks good")
        return True

def check_docker_compose():
    """Validate docker-compose.yml"""
    compose_path = "docker-compose.yml"
    if not os.path.exists(compose_path):
        print("❌ docker-compose.yml not found")
        return False
    
    with open(compose_path, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check for required services
    if "web:" not in content:
        issues.append("Missing web service")
    
    if "nginx:" not in content:
        issues.append("Missing nginx service")
    
    if "static_volume:" not in content:
        issues.append("Missing static_volume")
    
    if "healthcheck:" not in content:
        issues.append("Missing health checks")
    
    if issues:
        print(f"❌ docker-compose.yml issues: {', '.join(issues)}")
        return False
    else:
        print("✅ docker-compose.yml looks good")
        return True

def check_nginx_config():
    """Validate nginx configuration"""
    nginx_path = "nginx/default.conf"
    if not os.path.exists(nginx_path):
        print("❌ nginx/default.conf not found")
        return False
    
    with open(nginx_path, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check for required sections
    if "location /static/" not in content:
        issues.append("Missing static file location")
    
    if "proxy_pass http://web:8000" not in content:
        issues.append("Missing proxy pass to web service")
    
    if "location /health/" not in content:
        issues.append("Missing health check location")
    
    if issues:
        print(f"❌ nginx configuration issues: {', '.join(issues)}")
        return False
    else:
        print("✅ nginx configuration looks good")
        return True

def check_entrypoint():
    """Validate entrypoint script"""
    entrypoint_path = "entrypoint.prod.sh"
    if not os.path.exists(entrypoint_path):
        print("❌ entrypoint.prod.sh not found")
        return False
    
    with open(entrypoint_path, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check for required commands
    if "python manage.py migrate" not in content:
        issues.append("Missing database migration")
    
    if "python manage.py collectstatic" not in content:
        issues.append("Missing static file collection")
    
    if "gunicorn" not in content:
        issues.append("Missing Gunicorn startup")
    
    if issues:
        print(f"❌ entrypoint script issues: {', '.join(issues)}")
        return False
    else:
        print("✅ entrypoint script looks good")
        return True

def check_settings():
    """Validate Django settings structure"""
    settings_path = "app/settings.py"
    if not os.path.exists(settings_path):
        print("❌ app/settings.py not found")
        return False
    
    with open(settings_path, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check for required settings
    if "STATIC_URL" not in content:
        issues.append("Missing STATIC_URL")
    
    if "STATIC_ROOT" not in content:
        issues.append("Missing STATIC_ROOT")
    
    if "MEDIA_URL" not in content:
        issues.append("Missing MEDIA_URL")
    
    if "MEDIA_ROOT" not in content:
        issues.append("Missing MEDIA_ROOT")
    
    if "ALLOWED_HOSTS" not in content:
        issues.append("Missing ALLOWED_HOSTS")
    
    if issues:
        print(f"❌ Django settings issues: {', '.join(issues)}")
        return False
    else:
        print("✅ Django settings look good")
        return True

def main():
    """Main validation function"""
    print("🔍 Validating Billing Backend Configuration")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("manage.py"):
        print("❌ Not in Django project root directory")
        sys.exit(1)
    
    # Check required files
    required_files = [
        ("Dockerfile", "Docker configuration"),
        ("docker-compose.yml", "Docker Compose configuration"),
        ("nginx/default.conf", "Nginx configuration"),
        ("entrypoint.prod.sh", "Production entrypoint"),
        ("app/settings.py", "Django settings"),
        ("app/urls.py", "Django URL configuration"),
        ("env.production.example", "Environment template"),
    ]
    
    all_files_exist = True
    for file_path, description in required_files:
        if not check_file_exists(file_path, description):
            all_files_exist = False
    
    if not all_files_exist:
        print("\n❌ Some required files are missing")
        sys.exit(1)
    
    print("\n🔧 Validating Configuration Files")
    print("-" * 40)
    
    # Validate each configuration file
    validations = [
        check_dockerfile,
        check_docker_compose,
        check_nginx_config,
        check_entrypoint,
        check_settings,
    ]
    
    all_valid = True
    for validation_func in validations:
        if not validation_func():
            all_valid = False
    
    print("\n" + "=" * 50)
    if all_valid:
        print("✅ All configurations look good! Ready for deployment.")
        print("\nNext steps:")
        print("1. Update your .env file with production values")
        print("2. Test locally with: docker-compose up")
        print("3. Deploy to Coolify following COOLIFY_DEPLOYMENT.md")
    else:
        print("❌ Some configuration issues found. Please fix them before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()
