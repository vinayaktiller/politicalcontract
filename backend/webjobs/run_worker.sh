#!/bin/bash
echo "========================================"
echo "Starting Celery Worker WebJob"
echo "========================================"

# Change to app directory
cd /home/site/wwwroot

# Activate virtual environment - CORRECTED NAME
source petitionenv/bin/activate

echo "Virtual environment activated"
echo "Python path: $(which python)"
echo "Python version: $(python --version)"

# Start the worker
python webjobs/celery_worker.py