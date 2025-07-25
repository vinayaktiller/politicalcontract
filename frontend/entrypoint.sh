#!/bin/sh
set -e

# Create or update .env file with backend URL
echo "GENERATE_SOURCEMAP=false" > .env

# Use different backend URL based on environment
if [ "$DOCKER_ENV" = "true" ]; then
  echo "REACT_APP_BACKEND_BASE_URL=http://host.docker.internal:8000" >> .env
else
  echo "REACT_APP_BACKEND_BASE_URL=http://127.0.0.1:8000" >> .env
fi

# Execute the command
exec "$@"