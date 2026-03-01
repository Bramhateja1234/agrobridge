# Use official Python 3.11 image (more stable than 3.14 for now)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE agro_platform.settings.prod

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Run collectstatic (using a dummy key to avoid build errors)
RUN SECRET_KEY=build-time-only-key python manage.py collectstatic --noinput

# Expose port (Render uses 10000 by default)
EXPOSE 10000

# Start Gunicorn (Binding to 0.0.0.0:$PORT which Render provides)
CMD gunicorn --bind 0.0.0.0:$PORT agro_platform.wsgi:application
