#!/usr/bin/env python
"""
Install Python dependencies for WebJob
"""
import os
import subprocess
import sys
import time

def install_dependencies():
    print("📦 Installing Python dependencies...")
    
    # Path to requirements.txt in the main app
    requirements_path = '/home/site/wwwroot/requirements.txt'
    
    if not os.path.exists(requirements_path):
        print(f"❌ requirements.txt not found at: {requirements_path}")
        return False
    
    print(f"✅ Found requirements.txt at: {requirements_path}")
    
    try:
        # Upgrade pip first
        print("⬆️ Upgrading pip...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      check=True, capture_output=True, text=True)
        
        # Install dependencies from requirements.txt
        print("📥 Installing dependencies from requirements.txt...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', requirements_path
        ], capture_output=True, text=True, cwd='/home/site/wwwroot')
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully!")
            if result.stdout:
                print("Installation output:", result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
            return True
        else:
            print("❌ Failed to install dependencies:")
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = install_dependencies()
    sys.exit(0 if success else 1)