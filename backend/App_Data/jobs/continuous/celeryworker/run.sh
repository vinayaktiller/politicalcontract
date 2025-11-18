#!/bin/bash
cd /home/site/wwwroot
source env/bin/activate
celery -A backend worker --loglevel=info
tree -I "petitionenv|__pycache__|migrations|*.pyc"
