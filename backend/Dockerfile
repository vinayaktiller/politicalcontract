# Use the official slim Python image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffer outputs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for PostgreSQL and building Python packages
RUN apt-get update && apt-get install -y \
    libpq-dev \
    build-essential

# Ensure that env variables are used for Django settings
ENV PYTHONPATH="/app"

# Install Python dependencies separately to optimize Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Set the default command for running Django with WebSockets support (Daphne)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "backend.asgi:application"]

