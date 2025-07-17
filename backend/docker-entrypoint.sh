#!/bin/sh

# Wait for Redis to be ready
until nc -z redis 6379; do
  echo "Waiting for Redis..."
  sleep 1
done

# Wait for local PostgreSQL to be ready (using host.docker.internal)
until nc -z host.docker.internal 5432; do
  echo "Waiting for PostgreSQL..."
  sleep 1
done

# Run database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Execute the CMD from docker-compose
exec "$@"