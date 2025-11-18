import os
import zipfile
import tempfile
import shutil
from pathlib import Path

def create_webjob_package(script_name, webjob_name):
    """
    Create a zip package for WebJob deployment
    """
    print(f"Creating WebJob package for {webjob_name}...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        webjobs_dir = Path('webjobs')
        
        # Copy all necessary files
        files_to_copy = [
            'install_dependencies.py',
            f'{script_name}.py',
            f'run_{webjob_name}.cmd',
            'settings.job',
            '__init__.py'
        ]
        
        for file in files_to_copy:
            if (webjobs_dir / file).exists():
                shutil.copy(webjobs_dir / file, temp_dir)
                print(f"✅ Copied: {file}")
            else:
                print(f"❌ Missing: {file}")
                return None
        
        # Create zip file
        zip_filename = f'webjob_{webjob_name}.zip'
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in Path(temp_dir).iterdir():
                zipf.write(file_path, file_path.name)
        
        print(f"✅ Created: {zip_filename}")
        return zip_filename
        
    except Exception as e:
        print(f"❌ Error creating {webjob_name} package: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Clean up
        shutil.rmtree(temp_dir)

def main():
    print("🚀 Starting WebJob Package Creation")
    print("=" * 50)
    print("NOTE: This approach installs dependencies in the WebJob")
    print("since no virtual environment is found in Azure deployment.")
    print("=" * 50)
    
    # Check if webjobs directory exists
    if not Path('webjobs').exists():
        print("❌ Error: 'webjobs' directory not found!")
        return
    
    # Create worker WebJob package
    worker_zip = create_webjob_package('celery_worker', 'worker')
    
    # Create beat WebJob package  
    beat_zip = create_webjob_package('celery_beat', 'beat')
    
    if worker_zip and beat_zip:
        print("\n" + "=" * 50)
        print("✅ WebJob packages created successfully!")
        print("\n📦 Generated files:")
        print(f"   - {worker_zip}")
        print(f"   - {beat_zip}")
        print("\n📋 Next steps:")
        print("1. Go to Azure Portal → Your App Service → WebJobs")
        print("2. DELETE the existing WebJobs first")
        print("3. Upload these NEW zip files as Continuous WebJobs")
        print("\n⚠️  Important: This will install dependencies in the WebJob environment")
        print("   since no virtual environment is deployed to Azure.")
    else:
        print("\n❌ Failed to create WebJob packages")

if __name__ == '__main__':
    main()