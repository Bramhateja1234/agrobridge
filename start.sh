#!/bin/bash

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn
gunicorn agro_platform.wsgi:application --bind 0.0.0.0:$PORT
