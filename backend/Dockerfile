# FROM python:3.10-slim

# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1
# ENV PORT=8000  
# # IMPORTANT: allows Railway to override $PORT

# WORKDIR /app

# RUN apt-get update && apt-get install -y \
#     build-essential \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt /app/requirements.txt
# RUN pip install --no-cache-dir -r /app/requirements.txt

# COPY . /app

# RUN mkdir -p /app/media/profile_pics

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project files AFTER installing dependencies
COPY . /app

# --- FIX 1: Create staticfiles directory ---
RUN mkdir -p /app/staticfiles

# --- FIX 2: Run collectstatic (required when DEBUG=False) ---
RUN python manage.py collectstatic --noinput

# --- FIX 3: Ensure media directory exists ---
RUN mkdir -p /app/media/profile_pics

CMD ["sh", "-c", "daphne -b 0.0.0.0 -p $PORT backend.asgi:application"]
