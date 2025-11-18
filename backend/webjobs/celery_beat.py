#!/usr/bin/env python
"""
Celery Beat Scheduler WebJob for Azure
This script runs as a continuous WebJob
"""
import os
import sys
import subprocess

print("🚀 Starting Celery Beat WebJob")

# First, try to install dependencies
try:
    print("📦 Checking/installing dependencies...")
    result = subprocess.run([
        sys.executable, '-m', 'pip', 'list'
    ], capture_output=True, text=True, cwd='/home/site/wwwroot')
    
    # Check if Django is installed
    if 'Django' not in result.stdout:
        print("❌ Django not found. Installing dependencies...")
        # Run the install script
        install_result = subprocess.run([
            sys.executable, 'webjobs/install_dependencies.py'
        ], capture_output=True, text=True, cwd='/home/site/wwwroot')
        
        if install_result.returncode != 0:
            print("❌ Failed to install dependencies")
            print("Install error:", install_result.stderr)
            sys.exit(1)
    else:
        print("✅ Django is already installed")
        
except Exception as e:
    print(f"❌ Error checking dependencies: {e}")
    sys.exit(1)

# Add project root to Python path
project_root = '/home/site/wwwroot'
sys.path.insert(0, project_root)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

print("=== Starting Celery Beat ===")
print(f"Project Root: {project_root}")
print(f"Python Path: {sys.path}")
print(f"Broker URL: {os.getenv('CELERY_BROKER_URL', 'Not set')}")

try:
    import django
    print("✅ Django imported successfully!")
    django.setup()
    
    from celery.bin import beat as celery_beat
    from backend.celery import app as celery_app

    print("✅ Celery imported successfully!")
    
    # Start celery beat scheduler
    beat = celery_beat.beat(app=celery_app)
    
    options = {
        'loglevel': 'INFO',
        'pidfile': None,
    }
    
    print("🚀 Celery beat scheduler starting...")
    beat.run(**options)
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Available packages:")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True)
        print("Installed packages:")
        print(result.stdout)
    except:
        print("Could not list packages")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)