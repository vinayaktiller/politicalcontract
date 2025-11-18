#!/bin/bash
echo "========================================"
echo "WebJob Startup Script"
echo "========================================"

cd /home/site/wwwroot

# Install dependencies if not present
if ! python -c "import django" &> /dev/null; then
    echo "Django not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the appropriate service based on WebJob name
if [[ "$1" == "worker" ]]; then
    echo "Starting Celery Worker..."
    python webjobs/celery_worker.py
elif [[ "$1" == "beat" ]]; then
    echo "Starting Celery Beat..."
    python webjobs/celery_beat.py
else
    echo "Unknown WebJob type: $1"
    exit 1
fi