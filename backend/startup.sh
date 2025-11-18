#!/bin/bash
daphne -b 0.0.0.0 -p 8000 backend.asgi:application &
celery -A backend worker --loglevel=info &
celery -A backend beat --loglevel=info &
wait -n
exit $?
