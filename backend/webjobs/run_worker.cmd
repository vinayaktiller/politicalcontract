@echo off
cd /d %HOME%\site\wwwroot
echo ========================================
echo Starting Celery Worker WebJob
echo ========================================

echo Installing dependencies...
python webjobs\install_dependencies.py

echo Starting Celery Worker...
python webjobs\celery_worker.py