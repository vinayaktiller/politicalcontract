#!/bin/sh

# Default to "local" if not set
APP_ENV=${APP_ENV:-local}

if [ "$APP_ENV" = "railway" ]; then
  echo "🔧 Using Railway config..."

  # Extract PostgreSQL host and port from DATABASE_URL
  DB_HOST=$(echo "$DATABASE_URL" | sed -E 's/^.+@([^:]+):([0-9]+)\/.+$/\1/')
  DB_PORT=$(echo "$DATABASE_URL" | sed -E 's/^.+@([^:]+):([0-9]+)\/.+$/\2/')

  # Extract Redis host and port from REDIS_URL
  REDIS_HOST=$(echo "$REDIS_URL" | sed -E 's/^.+@([^:]+):([0-9]+)\/?.*$/\1/')
  REDIS_PORT=$(echo "$REDIS_URL" | sed -E 's/^.+@([^:]+):([0-9]+)\/?.*$/\2/')

else
  echo "🧪 Using Local Docker config..."

  DB_HOST="host.docker.internal"
  DB_PORT=5432

  REDIS_HOST="pfs-rds.canadacentral.redis.azure.net"
  REDIS_PORT=10000
fi

# Wait for Redis to be ready
until nc -z "$REDIS_HOST" "$REDIS_PORT"; do
  echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
  sleep 1
done

# Wait for PostgreSQL to be ready
until nc -z "$DB_HOST" "$DB_PORT"; do
  echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
  sleep 1
done

echo "✅ Services are up. Running Django setup..."

# Run Django setup
python manage.py migrate
python manage.py collectstatic --noinput

# Run whatever CMD is passed
exec "$@"
