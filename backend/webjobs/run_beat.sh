#!/bin/bash
echo "========================================"
echo "Starting Celery Beat WebJob"
echo "========================================"

# Change to app directory
cd /home/site/wwwroot

# Activate virtual environment - CORRECTED NAME
source petitionenv/bin/activate

echo "Virtual environment activated"
echo "Python path: $(which python)"
echo "Python version: $(python --version)"

# Start the beat scheduler
python webjobs/celery_beat.py