#!/bin/sh
set -e

# Create or update .env file with backend URL
echo "GENERATE_SOURCEMAP=false" > .env
echo "CHOKIDAR_USEPOLLING=true" >> .env
echo "WATCHPACK_POLLING=true" >> .env

# Use different backend URL based on environment
if [ "$APP_ENV" = "production" ]; then
  echo "REACT_APP_BACKEND_BASE_URL=http://backend:8000" >> .env
else
  echo "REACT_APP_BACKEND_BASE_URL=http://host.docker.internal:8000" >> .env
fi

# Execute the command
exec "$@"