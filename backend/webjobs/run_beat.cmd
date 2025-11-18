@echo off
cd /d %HOME%\site\wwwroot
echo ========================================
echo Starting Celery Beat WebJob
echo ========================================

echo Installing dependencies...
python webjobs\install_dependencies.py

echo Starting Celery Beat...
python webjobs\celery_beat.py